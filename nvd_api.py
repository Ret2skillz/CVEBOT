import requests
import json
import datetime
import asyncio
import aiohttp

class NVDAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://services.nvd.nist.gov/rest/json/cves/2.0'
        self.cwe_pwn_list = [
    "CWE-119", "CWE-120", "CWE-125", "CWE-787", "CWE-193", "CWE-416", "CWE-415",
    "CWE-476", "CWE-672", "CWE-401", "CWE-763", "CWE-122", "CWE-134", "CWE-706",
    "CWE-773", "CWE-190", "CWE-191", "CWE-681", "CWE-682", "CWE-131", "CWE-843",
    "CWE-704", "CWE-670", "CWE-94", "CWE-77", "CWE-78", "CWE-913", "CWE-362",
    "CWE-367", "CWE-667", "CWE-662", "CWE-209", "CWE-203"
    ]
        self.today = datetime.datetime.now().strftime("%Y-%m-%dT23:59:59.999")
        self.yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        self.yesterday.strftime("%Y-%m-%dT00:00:00.000")
        self.headers = {"apiKey": self.api_key}

    
    def fetch_daily_pwn(self):
        all_cve = []
        cwe_list = self.cwe_pwn_list
        pub_start_date = self.yesterday
        pub_end_date = self.today

        for cwe_id in cwe_list:
            try:
               url = self.base_url
               params = {
                   "pubStartDate": pub_start_date,
                   "pubEndDate": pub_end_date,
                   "cweId": cwe_id
               } 

               response = requests.get(url, params=params, headers=self.headers)
               if response.status_code == 200:
                    data = response.json()
                    if 'vulnerabilities' in data:
                        for vuln in data['vulnerabilities']:
                            cve_item = {
                            'id': vuln['cve']['id'],
                            'description': vuln['cve']['descriptions'][0]['value'] if vuln['cve']['descriptions'] else "No description available",
                            'published': vuln['cve']['published'],
                            'cwe': cwe_id,
                            'cvss': None,
                            'url': f"https://nvd.nist.gov/vuln/detail/{vuln['cve']['id']}"
                        }
                        
                        # Extract CVSS score if available
                            if 'metrics' in vuln['cve'] and 'cvssMetricV31' in vuln['cve']['metrics']:
                                cve_item['cvss'] = vuln['cve']['metrics']['cvssMetricV31'][0]['cvssData']['baseScore']

                            all_cve.append(cve_item)

                    else:
                        print('FAIIIIIIIIILED')

                    #asyncio.sleep(1)
            except Exception as e:
                print('FAIIILED FETCHING CWEEEE NO PWNNN AHHHHHH')
        return all_cve
    
    async def fetch_pwn(self, start_date, end_date):
        all_cve = []

        async with aiohttp.ClientSession() as session:
            for cwe_id in self.cwe_pwn_list:
                try:
                    url = self.base_url
                    params = {
                        "pubStartDate": start_date,
                        "pubEndDate": end_date,
                        "cweId": cwe_id
                    }

                    async with session.get(url, params=params, headers=self.headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'vulnerabilities' in data:
                                for vuln in data['vulnerabilities']:
                                    cve_item = {
                                        'id': vuln['cve']['id'],
                                        'description': vuln['cve']['descriptions'][0]['value'] if vuln['cve']['descriptions'] else "No description available",
                                        'published': vuln['cve']['published'],
                                        'cwe': cwe_id,
                                        'cvss': None,
                                        'url': f"https://nvd.nist.gov/vuln/detail/{vuln['cve']['id']}"
                                    }

                                    if 'metrics' in vuln['cve'] and 'cvssMetricV31' in vuln['cve']['metrics']:
                                        cve_item['cvss'] = vuln['cve']['metrics']['cvssMetricV31'][0]['cvssData']['baseScore']

                                    all_cve.append(cve_item)
                        else:
                            print(f"Failed to fetch for {cwe_id}: Status {response.status}")
                except Exception as e:
                    print(f"Exception while fetching {cwe_id}: {e}")

        return all_cve
    
    def list_cwe_pwn(self):
        return self.cwe_pwn_list




