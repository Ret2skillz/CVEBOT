import asyncio
import datetime
import time
from typing import Optional, Dict, List, Any

import aiohttp
import logging

log = logging.getLogger(__name__)

# Simple in-memory TTL cache
_CPE_CACHE: Dict[str, Any] = {}
_CPE_CACHE_TTL = 24 * 60 * 60  # seconds


class NVDAPI:
    """
    Minimal NVD API wrapper using the cpematch endpoint to resolve CPEs.

    Behavior:
    - resolve_cpe_matchstring uses cpematch/2.0?matchStringSearch=... and optionally
      lastModStartDate/lastModEndDate to restrict match-criteria to a time window.
    - _query_nvd will, when given a product with a wildcard match-string, resolve concrete CPEs
      via resolve_cpe_matchstring and then run CVE queries per concrete CPE (batching).
    - If product['strict'] is True and resolution yields no concrete CPEs, returns [] (no fallback).
    """

    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key or ""
        self.base_cve_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.base_cpematch_url = "https://services.nvd.nist.gov/rest/json/cpematch/2.0"
        self.headers = {"apiKey": self.api_key} if self.api_key else {}

        now = datetime.datetime.utcnow()
        self.today = now.strftime("%Y-%m-%dT23:59:59.999")
        self.yesterday = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000")
        self.week_ago = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%dT00:00:00.000")
        self.month_ago = (now - datetime.timedelta(days=30)).strftime("%Y-%m-%dT00:00:00.000")
        self.trimester_ago = (now - datetime.timedelta(days=119)).strftime("%Y-%m-%dT00:00:00.000")

        # original CWE list kept for non-product "pwn" searches
        self.cwe_pwn_list = [
            "CWE-119", "CWE-120", "CWE-125", "CWE-787", "CWE-193", "CWE-416",
            "CWE-415", "CWE-476", "CWE-672", "CWE-401", "CWE-763", "CWE-122",
            "CWE-134", "CWE-706", "CWE-773", "CWE-190", "CWE-191", "CWE-681",
            "CWE-682", "CWE-131", "CWE-843", "CWE-704", "CWE-670", "CWE-94",
            "CWE-77", "CWE-78", "CWE-913", "CWE-362", "CWE-367", "CWE-667",
            "CWE-662", "CWE-209", "CWE-203"
        ]

    async def resolve_cpe_matchstring(self, match_string: str, last_mod_start: Optional[str] = None, last_mod_end: Optional[str] = None, results_per_page: int = 500) -> List[str]:
        """
        Resolve concrete CPEs using the cpematch endpoint.
        Example: GET /rest/json/cpematch/2.0?matchStringSearch=cpe:2.3:*:tenda:*...&lastModStartDate=...&lastModEndDate=...
        Returns a list of concrete cpe23Uri / cpeName strings.
        """
        if not match_string:
            return []

        cache_key = (match_string, last_mod_start, last_mod_end)
        now_ts = time.time()
        cache = _CPE_CACHE.get(cache_key)
        if cache and now_ts - cache["ts"] < _CPE_CACHE_TTL:
            return cache["cpes"][:]

        cpe_names: List[str] = []
        start_index = 0

        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    "matchStringSearch": match_string,
                    "startIndex": start_index,
                    "resultsPerPage": results_per_page
                }
                if last_mod_start and last_mod_end:
                    params["lastModStartDate"] = last_mod_start
                    params["lastModEndDate"] = last_mod_end

                try:
                    async with session.get(self.base_cpematch_url, params=params, headers=self.headers) as resp:
                        if resp.status != 200:
                            log.debug("cpematch status %s for %s", resp.status, match_string)
                            break
                        data = await resp.json()
                except Exception as e:
                    log.debug("cpematch exception for %s: %s", match_string, e)
                    break

                # Response structure: results.matchStrings is expected
                result = data.get("results") or data.get("result") or data
                match_strings = []
                if isinstance(result, dict):
                    match_strings = result.get("matchStrings") or []

                if not match_strings:
                    break

                for ms in match_strings:
                    # Many responses wrap the match-string under "matchString": {"criteria": "..."}
                    # and may include "matches": [ { "cpeName": "...", "cpe23Uri": "..." }, ... ]
                    if isinstance(ms, dict):
                        # If there are concrete matches, use their cpe names
                        matches = ms.get("matches") or []
                        if matches:
                            for m in matches:
                                if isinstance(m, dict):
                                    cpe_uri = m.get("cpe23Uri") or m.get("cpeName")
                                    if cpe_uri:
                                        cpe_names.append(cpe_uri)
                            continue
                        # Else, check for matchString.criteria which can be a concrete cpe string
                        mstr = ms.get("matchString") or {}
                        crit = None
                        if isinstance(mstr, dict):
                            crit = mstr.get("criteria") or mstr.get("matchString") or None
                        if crit:
                            cpe_names.append(crit)
                            continue
                # pagination
                total = 0
                try:
                    total = int((result.get("totalResults") or result.get("total") or 0))
                except Exception:
                    total = 0

                start_index += results_per_page
                if total and start_index >= total:
                    break

                if len(match_strings) < results_per_page:
                    break

                await asyncio.sleep(0.02)

        # cache and return
        _CPE_CACHE[cache_key] = {"ts": now_ts, "cpes": cpe_names[:]}
        return cpe_names

    async def _single_cve_query(self, params: Dict[str, Any]) -> List[Dict]:
        """
        Query CVE API with provided params and return normalized list of vulns.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_cve_url, params=params, headers=self.headers) as resp:
                    if resp.status != 200:
                        log.debug("CVE API returned %s for params %s", resp.status, params)
                        return []
                    data = await resp.json()
        except Exception as e:
            log.debug("CVE request failed for params %s: %s", params, e)
            return []

        vulns = data.get("vulnerabilities") or []
        out: List[Dict] = []
        for item in vulns:
            try:
                cve = item.get("cve", {})
                cve_id = cve.get("id")
                descriptions = cve.get("descriptions", []) or []
                description = ""
                for d in descriptions:
                    if d.get("lang") == "en":
                        description = d.get("value", "")
                        break
                if not description and descriptions:
                    description = descriptions[0].get("value", "")
                published = cve.get("published") or cve.get("publishedDate")
                cwe = None
                problem_types = cve.get("problemTypes") or cve.get("problemtype")
                if isinstance(problem_types, list):
                    for pt in problem_types:
                        for dd in pt.get("description", []) or []:
                            v = dd.get("value", "")
                            if v and v.startswith("CWE-"):
                                cwe = v
                                break
                        if cwe:
                            break
                cvss = None
                metrics = cve.get("metrics") or {}
                if isinstance(metrics, dict):
                    v3 = metrics.get("cvssMetricV31") or metrics.get("cvssMetricV30") or metrics.get("cvssMetricV3")
                    if v3 and isinstance(v3, list) and v3:
                        cvss = v3[0].get("cvssData", {}).get("baseSeverity") or v3[0].get("cvssData", {}).get("baseScore")
                    v2 = metrics.get("cvssMetricV2")
                    if not cvss and v2 and isinstance(v2, list) and v2:
                        cvss = v2[0].get("cvssData", {}).get("baseSeverity") or v2[0].get("cvssData", {}).get("baseScore")
                url = f"https://nvd.nist.gov/vuln/detail/{cve_id}" if cve_id else None
                out.append({
                    "id": cve_id,
                    "description": description or "No description available",
                    "published": published,
                    "cwe": cwe,
                    "cvss": cvss,
                    "url": url
                })
            except Exception:
                continue
        return out

    async def _query_nvd(self, params: Dict[str, Any], product: Optional[Dict] = None, batch_size: int = 10) -> List[Dict]:
        """
        If product provided with wildcard match-string, resolve via cpematch and batch cve queries.
        Keep pubStartDate/pubEndDate in params to filter CVEs by publish date.
        """
        base_params = dict(params)
        strict = bool(product.get("strict", False)) if product else False

        # derive last-mod window from pubStartDate/pubEndDate
        last_mod_start = base_params.get("pubStartDate") or base_params.get("lastModStartDate")
        last_mod_end = base_params.get("pubEndDate") or base_params.get("lastModEndDate")

        if product:
            cpe = product.get("cpe")
            keyword = product.get("keyword")
            if cpe:
                # wildcard -> resolve matchstring via cpematch (simple)
                if "*" in cpe or ":*" in cpe:
                    cpe_names = await self.resolve_cpe_matchstring(cpe, last_mod_start=last_mod_start, last_mod_end=last_mod_end)
                    if not cpe_names:
                        if strict:
                            return []
                        # no cpes -> optionally fallback to keyword
                        if keyword:
                            base_params["keyword"] = keyword
                            return await self._single_cve_query(base_params)
                        return []
                    all_results: List[Dict] = []
                    for i in range(0, len(cpe_names), batch_size):
                        batch = cpe_names[i:i+batch_size]
                        for concrete in batch:
                            local = dict(base_params)
                            local["cpeName"] = concrete
                            vulns = await self._single_cve_query(local)
                            if vulns:
                                all_results.extend(vulns)
                            await asyncio.sleep(0.02)
                    # dedupe
                    unique: Dict[str, Dict] = {}
                    for v in all_results:
                        if v and v.get("id"):
                            unique[v["id"]] = v
                    return list(unique.values())
                else:
                    base_params["cpeName"] = cpe
            elif keyword:
                if strict:
                    return []
                base_params["keyword"] = keyword

        return await self._single_cve_query(base_params)

    # Range helpers
    async def fetch_range_pwn(self, pub_start_date: str, pub_end_date: str, severity: Optional[str] = None, product: Optional[Dict] = None) -> List[Dict]:
        # If product specified, query CVE API directly for date range (no CWE loop)
        if product:
            params = {"pubStartDate": pub_start_date, "pubEndDate": pub_end_date}
            if severity:
                params["cvssV3Severity"] = severity.upper()
            return await self._query_nvd(params, product=product)

        # Otherwise original CWE loop
        all_cve = []
        for cwe_id in self.cwe_pwn_list:
            params = {"pubStartDate": pub_start_date, "pubEndDate": pub_end_date, "cweId": cwe_id}
            if severity:
                params["cvssV3Severity"] = severity.upper()
            vulns = await self._query_nvd(params, product=None)
            if vulns:
                for v in vulns:
                    if not v.get("cwe"):
                        v["cwe"] = cwe_id
                all_cve.extend(vulns)
        # dedupe
        unique = {}
        for v in all_cve:
            if v and v.get("id"):
                unique[v["id"]] = v
        return list(unique.values())

    async def fetch_daily_pwn(self, severity: Optional[str] = None, product: Optional[Dict] = None) -> List[Dict]:
        return await self.fetch_range_pwn(self.yesterday, self.today, severity=severity, product=product)

    async def fetch_weekly_pwn(self, severity: Optional[str] = None, product: Optional[Dict] = None) -> List[Dict]:
        return await self.fetch_range_pwn(self.week_ago, self.today, severity=severity, product=product)

    async def fetch_monthly_pwn(self, severity: Optional[str] = None, product: Optional[Dict] = None) -> List[Dict]:
        return await self.fetch_range_pwn(self.month_ago, self.today, severity=severity, product=product)

    async def fetch_trimester_pwn(self, severity: Optional[str] = None, product: Optional[Dict] = None) -> List[Dict]:
        return await self.fetch_range_pwn(self.trimester_ago, self.today, severity=severity, product=product)

    async def fetch_custom_pwn(self, days: int, base_date: str = "", severity: Optional[str] = None, product: Optional[Dict] = None) -> List[Dict]:
        if base_date:
            try:
                base = datetime.datetime.strptime(base_date, "%Y-%m-%d")
            except Exception:
                base = datetime.datetime.utcnow()
        else:
            base = datetime.datetime.utcnow()
        end = base.strftime("%Y-%m-%dT23:59:59.999")
        start = (base - datetime.timedelta(days=days)).strftime("%Y-%m-%dT00:00:00.000")
        return await self.fetch_range_pwn(start, end, severity=severity, product=product)

    async def fetch_by_id(self, cve_id: str, product: Optional[Dict] = None) -> List[Dict]:
        params = {"cveId": cve_id}
        return await self._query_nvd(params, product=product)