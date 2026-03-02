import logging
import requests

log = logging.getLogger(__name__)

# Category keyword mappings used when searching for audit targets
AUDIT_CATEGORIES = {
    "emulator": "emulator OR emulation",
    "vm": "virtual machine OR hypervisor",
    "server": "server",
    "lib": "parser",
    "crypto": "crypto OR cryptography OR cipher",
        # Reduced logic to avoid >5 operators error
        # GitHub limit is 5 operators (AND/OR/NOT).
        # We need to be careful with "all" which combines many ORs.
        # "emulator OR network OR parser OR crypto" = 3 operators.
        # Plus filter criteria.
        "all": "emulator OR network OR parser OR crypto",
}


class GITHUBAPI:
    def __init__(self, github_key):
        self.github_key = github_key
        self.base_url = "https://api.github.com/search/"
        self.headers = {
            "Accept": 'application/vnd.github+json',
            "X-Github-Api-Version": "2022-11-28",
            "User-Agent": "CVE_BOT"
        }
        if self.github_key and self.github_key.strip():
            self.headers["Authorization"] = f"Bearer {self.github_key}"

    async def fetch_poc(self, cve_id):
        all_repos = []

        
        try:
            url = self.base_url + "repositories"
            params = {
                "q": f"{cve_id} in:name"
            }

            response = requests.get(url, params=params, headers=self.headers)
            if response.status_code == 401 and "Authorization" in self.headers:
                print("GitHub API returned 401 Unauthorized for PoC. Retrying without token...")
                headers_no_auth = self.headers.copy()
                headers_no_auth.pop("Authorization")
                response = requests.get(url, params=params, headers=headers_no_auth)

            print(response)
            if response.status_code == 200:
                data = response.json()
                if 'items' in data:
                    for repo in data['items']:
                        repo_item = {
                            'name': repo['name'],
                            'owner': repo['owner']['login'],
                            'url': repo['html_url']
                            }

                        all_repos.append(repo_item)
                else:
                    print('No PoC FounD')

        except Exception as e:
            print('FAILED REPOOOOOS')

        return all_repos

    async def fetch_audit_targets(
            self, 
            category: str = "all", 
            stale: bool = True, 
            min_stars: int = 10,
            max_stars: int = 500,
            min_size: int = 10,
            max_size: int = 10000,
            min_forks: int = 0,
            max_forks: int = 0,
            page: int = 1
    ):
        """
        Search GitHub for small/medium C or C++ repositories that are good candidates
        for handling vulnerability auditing.

        Parameters
        ----------
        category : one of the keys in AUDIT_CATEGORIES
        stale    : if True, only return repos not pushed since 2021 (forgotten projects);
                   otherwise no push date restriction.
        min_stars: minimum number of stargazers
        max_stars: maximum number of stargazers
        min_size : minimum repo size in KB
        max_size : maximum repo size in KB
        min_forks: minimum number of forks (0 = no minimum)
        max_forks: maximum number of forks (0 = no maximum)
        page     : result page (1-based, 10 results per page)
        """
        keywords = AUDIT_CATEGORIES.get(category, AUDIT_CATEGORIES["all"])

        # size in KB
        size_filter = f"size:{min_size}..{max_size}"

        # stars filter
        stars_filter = f"stars:{min_stars}..{max_stars}"

        # forks filter
        forks_filter = ""
        if min_forks > 0 and max_forks > 0:
            forks_filter = f"forks:{min_forks}..{max_forks}"
        elif min_forks > 0:
            forks_filter = f"forks:>={min_forks}"
        elif max_forks > 0:
            forks_filter = f"forks:0..{max_forks}"

        activity_filter = ""
        if stale:
            activity_filter = "pushed:<2021-01-01"

        repos = []
        
        # We need to fetch both C and C++ repos.
        # Direct OR in the query (language:C OR language:C++) proved unreliable/broken in testing
        # with these filters (returned 0 results).
        # To fix this, we'll fetch them separately and merge the results.
        # We'll split the page count to get roughly half/half.
        
        langs = ["language:C", "language:C++"]
        
        # We want 'per_page' total items. So we fetch per_page // 2 from each.
        # If per_page is 10, we fetch 5 C and 5 C++.
        limit_per_lang = 5 
        
        for lang in langs:
            # Construct query for this specific language
            # Note: We use parentheses around keywords to ensure logical grouping
            query = f"({keywords}) {lang} {size_filter} {stars_filter}"
            if forks_filter:
                query += f" {forks_filter}"
            if activity_filter:
                query += f" {activity_filter}"
            
            try:
                url = self.base_url + "repositories"
                params = {
                    "q": query,
                    "sort": "updated",
                    "order": "asc" if stale else "desc",
                    "per_page": limit_per_lang,
                    "page": page,
                }
                response = requests.get(url, params=params, headers=self.headers)
                
                # Handle 401 retry
                if response.status_code == 401 and "Authorization" in self.headers:
                    log.warning("GitHub API 401 for %s. Retrying without token...", lang)
                    headers_no_auth = self.headers.copy()
                    headers_no_auth.pop("Authorization")
                    response = requests.get(url, params=params, headers=headers_no_auth)

                if response.status_code == 200:
                    data = response.json()
                    for repo in data.get("items", []):
                        repos.append({
                            "name": repo["name"],
                            "owner": repo["owner"]["login"],
                            "url": repo["html_url"],
                            "stars": repo.get("stargazers_count", 0),
                            "forks": repo.get("forks_count", 0),
                            "size_kb": repo.get("size", 0),
                            "language": repo.get("language", "N/A"),
                            "last_push": repo.get("pushed_at", "N/A"),
                            "description": repo.get("description") or "No description",
                        })
                else:
                    log.warning("GitHub search failed for %s: %s %s", lang, response.status_code, response.text)
                    
            except Exception as e:
                log.error("fetch_audit_targets error for %s: %s", lang, e)

        # Sort combined results by update time to maintain some order
        # But since we paginate, this sort is only local to the page. 
        # This is an acceptable trade-off for reliability.
        repos.sort(key=lambda x: x["last_push"], reverse=not stale)
        
        return repos

    def fetch_has_releases(self, owner: str, repo_name: str) -> bool:
        """Check if a repo has any GitHub releases. Returns False on error."""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo_name}/releases"
            params = {"per_page": 1}
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return len(response.json()) > 0
            return False
        except Exception as e:
            log.warning("fetch_has_releases error for %s/%s: %s", owner, repo_name, e)
            return False

