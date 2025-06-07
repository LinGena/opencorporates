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
import shutil
from pyvirtualdisplay import Display
from utils.func import write_to_file_json, load_from_file_json
from concurrent.futures import ThreadPoolExecutor, as_completed
import undetected_chromedriver as uc

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

os.environ['PYVIRTUALDISPLAY_DISPLAYFD'] = '0'

def accounts():
    for i in range(0, 300):
        CreateAccount().create_account_cookies()


def parse(first_start: bool = False):
    # if not settings.sets.debug:
    #     _display = Display(visible=False, size=(1920, 1080))
    #     _display.start()
    try:
        proxies_list = load_from_file_json('proxy/proxies_list.json')
        client = Scraper(proxies_list, first_start)
        client.run()
        first_start = False
    except Exception as ex:
        print('[PARSE]',ex)
    finally:
        if 'client' in locals() and hasattr(client, 'close_driver'):
            client.close_driver()
        if 'client' in locals() and hasattr(client, 'close_connection'):
            client.close_connection()
        # if '_display' in locals():
        #     _display.stop()


# def parse_thread():
    # first_start = True
    # for i in range(settings.sets.count_thred):
    #     t = Thread(target=parse, args=(first_start,))
    #     t.start()
    #     print(f'Thread {i} started')
    #     first_start = False
    #     time.sleep(5)
def parse_thread():
    workers = settings.sets.count_thred        
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = set()
        for i in range(workers):
            fut = pool.submit(parse, i == 0) 
            futures.add(fut)
            print(f'Thread {i} started')
            time.sleep(5)
        while futures:
            done, _ = as_completed(futures, timeout=None), futures
            for f in done:
                futures.remove(f)
                if exc := f.exception():
                    print('[POOL EXCEPTION]', exc)
                futures.add(pool.submit(parse, False))



def check_db():
    IsDbCreated().check()
    IsDbTable().check()

def prepare_environment():
    """Чистим старые профили и заново инициализируем прокси-файл."""
    if os.path.exists('chrome_data'):
        shutil.rmtree('chrome_data')
    DbCompanies().clear_processing_status()
    proxies_list = get_proxies()
    write_to_file_json('proxy/proxies_list.json', proxies_list)

def first_run():
    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')
        driver = uc.Chrome(version_main=int(os.getenv('DRIVER_VERSION')), options=options)
        driver.quit()
    except:
        pass

if __name__ == "__main__":
    # check_db()
    # accounts()
    # parse()
    first_run()
    prepare_environment()
    parse_thread()



