import random
from bs4 import BeautifulSoup
from accounts.driver import UndetectedDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from geopy.geocoders import Nominatim
from db.db_cookies import DbCookies
from proxy.proxy_manager import get_proxies
# from proxy.get_proxy import get_proxy
from utils.func import *
import time


class GetSession(UndetectedDriver):
    def __init__(self, proxy_id: int = 1, first_start: bool = False):
        self.domain_name = "https://opencorporates.com"
        self.proxies_list = get_proxies()
        self.id_cookies = None
        proxy = self.get_proxy()
        self.initialize_driver(proxy, first_start)
        self.geolocator = Nominatim(user_agent=f"my_app_{proxy_id}", proxies={'http':proxy,'https':proxy}, timeout=15)  

    def get_proxy(self) -> dict:
        # return get_proxy()
        random.shuffle(self.proxies_list)
        return self.proxies_list[0]

    def initialize_driver(self, proxy: str, first_start: bool = False):
        # data_cookies = DbCookies().get_cookies()
        # if not data_cookies:
        #     raise Exception('There is no free cookies')
        # self.id_cookies = data_cookies['id']
        # super().__init__(proxy=proxy, is_capsolver=False, cookies=data_cookies['cookies'])
        super().__init__(proxy=proxy, is_capsolver=False, first_start=first_start)
        # self.check_current_proxy(proxy)
        self.add_to_driver_cookies()

    def check_current_proxy(self, proxy: str) -> bool:
        try:
            self.driver.get('https://api.ipify.org/?format=json')
            content = self.driver.page_source
            soup = BeautifulSoup(content,'html.parser')
            response = json.loads(soup.find('pre').text.strip())
            ip = proxy.split('@')[1].split(':')[0]
            if response['ip'] == ip:
                return True
        except Exception as ex:
            print('[check_current_proxy]',ex)
        raise Exception('proxies do not match')

    def add_to_driver_cookies(self):
        self.driver.get(self.domain_name)
        time.sleep(5)
        data_cookies = DbCookies().get_cookies()
        if not data_cookies:
            raise Exception('There is no free cookies')
        self.id_cookies = data_cookies['id']
        cookies_list = [{"name": key, "value": str(value)} for key, value in data_cookies['cookies'].items()]
        for cookie in cookies_list:
            self.driver.add_cookie(cookie)

    def get_page_content(self, url: str, count_try: int = 0) -> str:
        if not self.id_cookies:
            raise Exception('The cookies are needed.')
        if count_try >= 5:
            DbCookies().set_blocked(self.id_cookies)
            self.add_to_driver_cookies()
            self.get_page_content(url, 0) 
        src = self.get_response(url)
        if not src or 'log in to see this data' in src or '<title>' not in src:
            return self.get_page_content(url, count_try + 1)
        if '<body onload="go()">' in src:
            return self.get_page_content(url, count_try + 1)
        if '<title>Forbidden</title>' in src:
            raise Exception('BLOCK')
        return src
    
    def get_response(self, url: str) -> str:
        self.driver.get(url)
        try:
            self.wait(10, (By.XPATH, "//body[@class]"))
        except TimeoutException:
            write_to_file('error.html',self.driver.page_source)
            self.worker_close()
            self.initialize_driver(self.get_proxy())
            return self.get_response(url)
        return self.driver.page_source
    
    def worker_close(self):
        if self.id_cookies:
            DbCookies().change_status(self.id_cookies, 0)
        self.close_driver()