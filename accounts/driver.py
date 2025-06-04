import os
import shutil
import time
import uuid
import undetected_chromedriver as uc_webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from capsolver_extension_python import Capsolver
from config.settings import settings
from proxy.proxy_ext import load_proxy
from accounts.cookies_ext import load_cookies
from utils.logger import Logger


class UndetectedDriver:
    def __init__(self, proxy:str = None, is_capsolver: bool = False, cookies: str = None, first_start: bool = False):
        self.proxy = proxy
        self.first_start = first_start
        self.cookies = cookies
        self.is_capsolver = is_capsolver
        self.logger = Logger().get_logger(__name__)
        self.folder_path = f'{settings.base_path.dir}/accounts/chrome_data/{str(uuid.uuid4())}'
        self.__options = uc_webdriver.ChromeOptions()
        self._set_chromeoptions()
        self.driver = self._create_driver()
        self.wait = lambda time_w, criteria: WebDriverWait(self.driver, time_w).until(
            EC.presence_of_element_located(criteria))

    def close_driver(self):
        self._close_driver()
        self._del_folder()

    def _set_chromeoptions(self):
        extensions = []
        if self.cookies:
            cookies_extension_path = load_cookies('opencorporates.com', self.cookies, self.folder_path)
            extensions.append(cookies_extension_path)
        if self.proxy:
            proxy_extension_path = f'{self.folder_path}/proxy_ext'
            load_proxy(self.proxy, proxy_extension_path)
            extensions.append(proxy_extension_path)
        if self.is_capsolver:
            capsolver_path = Capsolver(settings.capsolver.token).load().split('=')[1]
            extensions.append(capsolver_path)
        if extensions:
            self.__options.add_argument(f"--load-extension={','.join(extensions)}")

        self.__options.add_argument('--ignore-ssl-errors=yes')
        self.__options.add_argument('--ignore-certificate-errors')
        self.__options.add_argument('--start-maximized')
        self.__options.add_argument('--no-sandbox')
        self.__options.add_argument('--disable-dev-shm-usage')
        self.__options.add_argument('--disable-setuid-sandbox')
        self.__options.add_argument('--disable-gpu')
        self.__options.add_argument('--disable-software-rasterizer')
        self.__options.add_argument('--disable-application-cache')
        self.__options.add_argument('--disk-cache-size=0')
        self.__options.add_argument('--headless=new')
        if self.proxy:
            self.__options.add_argument("--disable-features=WebRtcHideLocalIpsWithMdns")
            prefs = {
                "intl.accept_languages": "en-US,en",
                'enable_do_not_track': True,
                "webrtc.ip_handling_policy": "disable_non_proxied_udp",
                "webrtc.multiple_routes_enabled": False,
                "webrtc.nonproxied_udp_enabled": False
            }
            self.__options.add_experimental_option("prefs", prefs)

    def _create_driver(self):
        os.makedirs(self.folder_path, exist_ok=True)
        if settings.sets.debug:
            driver = uc_webdriver.Chrome(version_main=settings.sets.driver_version,
                                        user_data_dir=self.folder_path,
                                        options=self.__options)
        else:
            if self.first_start:
                driver = uc_webdriver.Chrome(version_main=settings.sets.driver_version,
                                            user_data_dir=self.folder_path,
                                            options=self.__options)
            else:
                driver = uc_webdriver.Chrome(version_main=settings.sets.driver_version,
                                            user_data_dir=self.folder_path,
                                            user_multi_procs=True,
                                            options=self.__options)
        return driver

    def _close_driver(self):
        if hasattr(self, "driver"):
            try:
                self.driver.close()
            except:
                pass
            try:
                self.driver.quit()
            except Exception as ex:
                pass
    
    def _del_folder(self):
        if os.path.exists(self.folder_path):
            try:
                time.sleep(5)
                shutil.rmtree(self.folder_path)
            except Exception as ex:
                self.logger.debug(ex)

    def move_and_click(self, element):
        chain = ActionChains(self.driver)
        chain.reset_actions()
        if element is not None:
            chain.move_to_element(element)
            chain.click()
        chain.perform()
        chain.reset_actions()