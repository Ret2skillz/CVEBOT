import csv
import io
import logging
import os

import requests

log = logging.getLogger(__name__)

# Public CSV export of the kCTF Vulnerability Rewards Program spreadsheet.
# Override via KCTF_SPREADSHEET_URL env variable if needed.
DEFAULT_KCTF_URL = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vS1REdTA29OJftst8xN5B5x8iIUcxuK6bXdzF8G1UXCmRtoNsoQ9MbebdRdFnj6qZ0Yd7LwQfvYC2oF/pub?output=csv"
)


class KCTFApi:
    """Fetches and parses the public kCTF VRP Google Spreadsheet."""

    def __init__(self, spreadsheet_url: str | None = None):
        self.spreadsheet_url = spreadsheet_url or os.getenv(
            "KCTF_SPREADSHEET_URL", DEFAULT_KCTF_URL
        )

    def _fetch_csv(self) -> list[dict]:
        """Download the spreadsheet as CSV and return a list of row dicts."""
        try:
            response = requests.get(self.spreadsheet_url, timeout=15)
            response.raise_for_status()
        except Exception as e:
            log.error("Failed to fetch kCTF spreadsheet: %s", e)
            return []

        text = response.content.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        rows = []
        for row in reader:
            # Normalise keys: strip whitespace
            rows.append({k.strip(): v.strip() for k, v in row.items() if k})
        return rows

    def fetch_latest(self, count: int = 10) -> list[dict]:
        """
        Return the *count* most-recent kCTF entries.

        Each entry dict contains at least:
          - issue   : bug-tracker link or identifier
          - commit  : associated kernel / source commit URL
          - captured: timestamp when the flag was captured
          - submitter: name of the submitter (if available)
          - reward  : reward amount (if available)

        The spreadsheet is ordered newest-first; we simply return the first
        *count* non-empty rows after skipping any header/metadata rows.
        """
        rows = self._fetch_csv()
        if not rows:
            return []

        # Detect column names dynamically — the spreadsheet uses human-readable
        # headers that may shift over time.  We look for common substrings.
        sample = rows[0]
        headers = list(sample.keys())

        def _find_col(*candidates):
            for c in candidates:
                for h in headers:
                    if c.lower() in h.lower():
                        return h
            return None

        col_issue = _find_col("issue", "cve", "bug", "id")
        col_commit = _find_col("commit", "fix", "patch", "cl")
        col_captured = _find_col("captur", "time", "date", "timestamp", "submitted")
        col_submitter = _find_col("submitter", "reporter", "author", "researcher")
        col_reward = _find_col("reward", "bounty", "amount")

        entries = []
        for row in rows:
            # Skip rows that look completely empty
            values = [v for v in row.values() if v]
            if not values:
                continue

            entry = {
                "issue": row.get(col_issue, "") if col_issue else "",
                "commit": row.get(col_commit, "") if col_commit else "",
                "captured": row.get(col_captured, "") if col_captured else "",
                "submitter": row.get(col_submitter, "") if col_submitter else "",
                "reward": row.get(col_reward, "") if col_reward else "",
            }
            # Include any extra columns not mapped above
            mapped = {col for col in [col_issue, col_commit, col_captured, col_submitter, col_reward] if col is not None}
            for h in headers:
                if h not in mapped:
                    entry[h] = row.get(h, "")
            entries.append(entry)
            if len(entries) >= count:
                break

        return entries
