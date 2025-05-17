from selenium.common.exceptions import TimeoutException
import random
import time
import threading
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from faker import Faker
from mailtm import Email
from accounts.driver import UndetectedDriver
# from proxy.get_proxy import get_proxy
from proxy.proxy_manager import get_proxies
from db.db_cookies import DbCookies


class CreateAccount(UndetectedDriver):
    def __init__(self):
        self.email_received = threading.Event()
        # proxy = get_proxy()
        self.proxies_list = get_proxies()
        proxy = self.get_proxy()
        super().__init__(proxy=proxy, is_capsolver=True)

    def get_proxy(self) -> dict:
        random.shuffle(self.proxies_list)
        return self.proxies_list[0]

    def create_account_cookies(self) -> None:
        try:
            self.driver.get('https://opencorporates.com/users/sign_up')
            self.check_ip_block()
            self.fill_fields()
            self.read_terms()
            self.check_captcha()
            self.btn_commit()
            if self.check_ip_block():
                link = self.get_email_verify()
                if link:
                    self.driver.get(link)
                    if self.wait_for_sign_in_message():
                        cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}
                        DbCookies().insert_data(cookies)
                        self.logger.debug('Cookies created and saved.')
        except Exception as ex:
            self.logger.error(ex)
        finally:
            self.close_driver()

    def fill_fields(self) -> None:
        self.get_fakers()
        self.input_rows('//*[@id="user_name"]', self.user_name)
        self.input_rows('//*[@id="user_email"]', self.user_email)
        self.input_rows('//*[@id="user_user_info_job_title"]', self.user_job_title)
        self.input_rows('//*[@id="user_user_info_company"]', self.user_company)
        self.input_rows('//*[@id="user_password"]', self.user_password)
        self.input_rows('//*[@id="user_password_confirmation"]', self.user_password)

    def get_fakers(self) -> None:
        fake = Faker()
        self.user_name = fake.first_name()
        self.user_job_title = fake.job()
        self.user_company = fake.company()
        self.user_password = fake.password()
        self.temp_mail_object = Email()
        email_username = self.user_name.lower() + fake.last_name().lower() + str(random.randint(1000, 9000))
        self.temp_mail_object.register(username=email_username)
        self.user_email = self.temp_mail_object.address
    
    def input_rows(self, xpath: str, value: str) -> None:
        input_field = self.get_element(xpath)
        input_field.send_keys(value)
        
    def get_element(self, xpath: str) -> WebElement:
        try:
            element = self.wait(60, (By.XPATH, xpath))
            return element
        except TimeoutException:
            raise Exception(f'Something wrong with xpath: {xpath}')
        
    def check_ip_block(self) -> bool:
        time.sleep(1)
        try:
            self.wait(10, (By.XPATH, "//body[@class]"))
            return True
        except TimeoutException:
            raise Exception('No body')

        
    def read_terms(self) -> None:
        read_field = self.driver.find_element(By.XPATH, '//div[@class="terms-conditions-box"]')
        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", read_field)
        check_box = self.get_element('//*[@id="user_terms_and_conditions"]')
        self.move_and_click(check_box)
        
    def btn_commit(self) -> None:
        try:
            element = self.wait(10, (By.NAME, "commit"))
            self.move_and_click(element)
        except TimeoutException:
            raise Exception('Something wrong with commit button')
    
    def check_captcha(self) -> None:
        try:
            iframe = self.wait(10, (By.XPATH, '//iframe[contains(@src, "google.com/recaptcha/api2/anchor")]'))
            self.driver.switch_to.frame(iframe)
            self.wait(60, (By.CSS_SELECTOR, ".recaptcha-checkbox-checked"))
            self.driver.switch_to.default_content()
        except TimeoutException:
            raise Exception('Something wrong with Re-Captcha')
        
    def get_email_verify(self) -> str:
        self.verification_link = None
        def listener(message):
            try:
                msg = message['text'] if message['text'] else message['html']
                self.verification_link = 'http://opencorporates.com/' + str(msg).split('http://opencorporates.com/')[1].split('>')[0]
                self.email_received.set()
                self.temp_mail_object.stop()
            except:
                pass
        self.temp_mail_object.start(listener)
        if not self.email_received.wait(timeout=120):
            raise Exception("Email verification link not received within timeout")
        return self.verification_link

    
    def wait_for_sign_in_message(self) -> bool:
        try:
            message_element = self.wait(30, (By.CSS_SELECTOR, '.oc-message--notice'))
            message_text = message_element.text
            if "You are now signed in." in message_text:
                return True
            else:
                self.logger.error(f"Unexpected message: {message_text}")
                return False
        except TimeoutException:
            raise Exception("Sign-in confirmation message not found.")

    
  