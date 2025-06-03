from accounts.create import CreateAccount
from db.core import IsDbCreated, IsDbTable
import warnings
import time
from threading import Thread
from scraper.scraper import Scraper
from config.settings import settings
from proxy.proxy_manager import get_proxies
from db.db_companies import DbCompanies
import os
from pyvirtualdisplay import Display

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

os.environ['PYVIRTUALDISPLAY_DISPLAYFD'] = '0'

def accounts():
    for i in range(0, 300):
        CreateAccount().create_account_cookies()


def parse(proxies_list: list, first_start: bool = False):
    while True:
        # if not settings.sets.debug:
        #     _display = Display(visible=False, size=(1920, 1080))
        #     _display.start()
        try:
            client = Scraper(proxies_list, first_start)
            client.run()
            first_start = False
        except Exception as ex:
            print(ex)
        finally:
            if 'client' in locals() and hasattr(client, 'close_driver'):
                client.close_driver()
            if 'client' in locals() and hasattr(client, 'close_connection'):
                client.close_connection()
            # if '_display' in locals():
            #     _display.stop()


def parse_thread():
    DbCompanies().clear_processing_status()
    proxies_list = get_proxies()
    first_start = True
    for i in range(settings.sets.count_thred):
        t = Thread(target=parse, args=(proxies_list, first_start))
        t.start()
        print(f'Thread {i} started')
        first_start = False
        time.sleep(5)


def check_db():
    IsDbCreated().check()
    IsDbTable().check()

if __name__ == "__main__":
    # check_db()
    # accounts()
    # parse()
    parse_thread()



