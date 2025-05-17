from curl_cffi import requests
import time
from db.db_cookies import DbCookies
from proxy.get_proxy import get_proxy


class GetSession():
    def __init__(self):
        self.id_cookies = None
        self.domain_name = "https://opencorporates.com"
        
    def get_page_content(self, url: str, count_try: int = 0) -> str:
        if count_try > 50:
            print(f'No content from page: {url}')
            return None
        src = self.get_response(url)
        if 'log in to see this data' in src:
            return self.get_page_content(url, count_try + 1)
        if '<body onload="go()">' in src:
            print("onload")
            time.sleep(1)
            return self.get_page_content(url, count_try + 1)
        print('Ok')
        return src

    def get_response(self, url: str, count_try: int = 0) -> str:
        if count_try > 3:
            return None
        try:
            self.session = self.create_session()
            proxy = get_proxy()
            proxies = {'http':proxy,'https':proxy}
            response = self.session.get(url, impersonate = "chrome124", timeout=10, proxies=proxies)
            response.raise_for_status()
            return response.text
        except Exception as ex:
            print(ex)
        finally:
            self.close_session()
        return self.get_response(url, count_try + 1)
    
    def create_session(self):
        session = requests.Session()
        session.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8,uk;q=0.7',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-arch': '"x86"',
            'sec-ch-ua-full-version': '"131.0.2903.99"',
            'sec-ch-ua-full-version-list': '"Microsoft Edge";v="131.0.2903.99", "Chromium";v="131.0.6778.140", "Not_A Brand";v="24.0.0.0"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"15.0.0"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)',
        }
        data_cookies = DbCookies().get_cookies()
        if not data_cookies:
            raise Exception('There is no free cookies')
        self.id_cookies = data_cookies['id']
        session.cookies.update(data_cookies['cookies'])
        proxy = get_proxy()
        session.proxies = {'http':proxy,'https':proxy}
        return session
    
    def close_session(self):
        if hasattr(self, "session"):
            self.session.close()