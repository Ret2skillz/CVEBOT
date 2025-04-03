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
        self.yesterday = self.yesterday.strftime("%Y-%m-%dT00:00:00.000")
        self.week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        self.week_ago = self.week_ago.strftime("%Y-%m-%dT00:00:00.000")
        self.month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        self.month_ago = self.month_ago.strftime("%Y-%m-%dT00:00:00.000")
        self.trimester_ago = datetime.datetime.now() - datetime.timedelta(days=119)
        self.trimester_ago = self.trimester_ago.strftime("%Y-%m-%dT00:00:00.000")
        self.headers = {"apiKey": self.api_key}

    
    async def fetch_daily_pwn(self, severity=None):
        all_cve = []
        pub_start_date = self.yesterday
        pub_end_date = self.today

        async with aiohttp.ClientSession() as session:
            for cwe_id in self.cwe_pwn_list:
                try:
                    url = self.base_url
                    params = {
                    "pubStartDate": pub_start_date,
                    "pubEndDate": pub_end_date,
                    "cweId": cwe_id,
                    **({"cvssV3Severity": severity.upper()} if severity else {})
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

                    
                except Exception as e:
                    print('FAIIILED FETCHING CWEEEE NO PWNNN AHHHHHH')
        return all_cve
    
    async def fetch_weekly_pwn(self, severity=None):
        all_cve = []
        start_date = self.week_ago
        end_date = self.today

        async with aiohttp.ClientSession() as session:
            for cwe_id in self.cwe_pwn_list:
                try:
                    url = self.base_url
                    params = {
                        "pubStartDate": start_date,
                        "pubEndDate": end_date,
                        "cweId": cwe_id,
                        **({"cvssV3Severity": severity.upper()} if severity else {})
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
    
    async def fetch_monthly_pwn(self, severity=None):
        all_cve = []
        start_date = self.month_ago
        end_date = self.today

        async with aiohttp.ClientSession() as session:
            for cwe_id in self.cwe_pwn_list:
                try:
                    url = self.base_url
                    params = {
                        "pubStartDate": start_date,
                        "pubEndDate": end_date,
                        "cweId": cwe_id,
                        **({"cvssV3Severity": severity.upper()} if severity else {})
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
    
    async def fetch_trimester_pwn(self, severity=None):
        all_cve = []
        start_date = self.trimester_ago
        end_date = self.today

        async with aiohttp.ClientSession() as session:
            for cwe_id in self.cwe_pwn_list:
                try:
                    url = self.base_url
                    params = {
                        "pubStartDate": start_date,
                        "pubEndDate": end_date,
                        "cweId": cwe_id,
                        **({"cvssV3Severity": severity.upper()} if severity else {})
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
    
    async def fetch_custom_pwn(self, range, date="", severity=None):
        all_cve = []
        if date == "":
            start_date = datetime.datetime.now() - datetime.timedelta(days=range)
            start_date = start_date.strftime("%Y-%m-%dT00:00:00.000")
            end_date = self.today
        else:
            try:
                parsed = datetime.datetime.strptime(date.strip(), "%Y-%m-%d")
                start_date = parsed - datetime.timedelta(days=range)
                start_date = start_date.strftime("%Y-%m-%dT00:00:00.000")
                end_date = parsed.strftime("%Y-%m-%dT23:59:59.999")
            except:
                print("Invalid date")
                return []

        async with aiohttp.ClientSession() as session:
            for cwe_id in self.cwe_pwn_list:
                try:
                    url = self.base_url
                    params = {
                        "pubStartDate": start_date,
                        "pubEndDate": end_date,
                        "cweId": cwe_id,
                        **({"cvssV3Severity": severity.upper()} if severity else {})
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
    
    async def fetch_by_id(self, cve_id):
        all_cve = []

        async with aiohttp.ClientSession() as session:
            try:
                url = self.base_url
                params = {
                    "cveId": cve_id
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
                                    'cvss': None,
                                    'url': f"https://nvd.nist.gov/vuln/detail/{vuln['cve']['id']}"
                                }

                                if 'metrics' in vuln['cve'] and 'cvssMetricV31' in vuln['cve']['metrics']:
                                    cve_item['cvss'] = vuln['cve']['metrics']['cvssMetricV31'][0]['cvssData']['baseScore']

                                all_cve.append(cve_item)
                    else:
                        print(f"Failed to fetch for {cve_id}: Status {response.status}")
            except Exception as e:
                print(f"Exception while fetching {cve_id}: {e}")

        return all_cve
    
    def list_cwe_pwn(self):
        return self.cwe_pwn_list




