import requests

# Category keyword mappings used when searching for audit targets
AUDIT_CATEGORIES = {
    "emulator": "emulator OR emulation",
    "vm": "\"virtual machine\" OR hypervisor",
    "server": "\"ftp server\" OR \"http server\" OR \"smtp server\" OR \"tcp server\"",
    "lib": "\"file parser\" OR \"image parser\" OR \"xml parser\" OR \"format parser\"",
    "crypto": "crypto OR cryptography OR cipher",
    "all": "emulator OR emulation OR \"ftp server\" OR \"http server\" OR \"file parser\" OR crypto OR hypervisor",
}


class GITHUBAPI:
    def __init__(self, github_key):
        self.github_key = github_key
        self.base_url = "https://api.github.com/search/"
        self.headers = {"Accept": 'application/vnd.github+json', "X-Github-Api-Version": "2022-11-28", "User-Agent": "CVE_BOT", "Authorization": f"Bearer {self.github_key}"}

    async def fetch_poc(self, cve_id):
        all_repos = []

        
        try:
            url = self.base_url + "repositories"
            params = {
                "q": f"{cve_id} in:name"
            }

            response = requests.get(url, params=params, headers=self.headers)
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

    async def fetch_audit_targets(self, category: str = "all", stale: bool = True, page: int = 1):
        """
        Search GitHub for small/medium C or C++ repositories that are good candidates
        for vulnerability auditing.

        Parameters
        ----------
        category : one of the keys in AUDIT_CATEGORIES
        stale    : if True, only return repos not pushed since 2021 (forgotten projects);
                   if False, return moderately-used active repos (stars 10..500)
        page     : result page (1-based, 10 results per page)
        """
        keywords = AUDIT_CATEGORIES.get(category, AUDIT_CATEGORIES["all"])

        # language filter covers both C and C++
        lang_filter = "language:C OR language:C++"

        # size in KB: 10 KB .. 10 MB — avoids empty toy repos and huge monorepos
        size_filter = "size:10..10000"

        if stale:
            # repos that have not been touched since the start of 2021
            activity_filter = "pushed:<2021-01-01"
        else:
            # moderately active repos
            activity_filter = "stars:10..500"

        query = f"({keywords}) {lang_filter} {size_filter} {activity_filter}"

        repos = []
        try:
            url = self.base_url + "repositories"
            params = {
                "q": query,
                "sort": "updated",
                "order": "asc" if stale else "desc",
                "per_page": 10,
                "page": page,
            }
            response = requests.get(url, params=params, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                for repo in data.get("items", []):
                    repos.append({
                        "name": repo["name"],
                        "owner": repo["owner"]["login"],
                        "url": repo["html_url"],
                        "stars": repo.get("stargazers_count", 0),
                        "size_kb": repo.get("size", 0),
                        "language": repo.get("language", "N/A"),
                        "last_push": repo.get("pushed_at", "N/A"),
                        "description": repo.get("description") or "No description",
                    })
            else:
                print(f"GitHub search returned {response.status_code}")
        except Exception as e:
            print(f"fetch_audit_targets error: {e}")

        return repos

