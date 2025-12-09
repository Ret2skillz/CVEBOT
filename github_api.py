import requests

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

