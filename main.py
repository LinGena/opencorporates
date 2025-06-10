from accounts.create import CreateAccount
from db.core import IsDbCreated, IsDbTable
import warnings
import time
import sys
from threading import Thread
from scraper.scraper import Scraper
from config.settings import settings
from proxy.proxy_manager import get_proxies
from db.db_companies import DbCompanies
import os
import shutil
from pyvirtualdisplay import Display
from utils.func import write_to_file_json, load_from_file_json
from concurrent.futures import (
    ThreadPoolExecutor, wait, FIRST_COMPLETED
)
import undetected_chromedriver as uc


warnings.filterwarnings('ignore', message='Unverified HTTPS request')

os.environ['PYVIRTUALDISPLAY_DISPLAYFD'] = '0'

def accounts():
    for i in range(0, 300):
        CreateAccount().create_account_cookies()


def parse(first_start: bool = False):
    if not settings.sets.debug:
        _display = Display(visible=False, size=(1920, 1080))
        _display.start()
    try:
        proxies_list = load_from_file_json('proxy/proxies_list.json')
        client = Scraper(proxies_list, first_start)
        client.run()
        first_start = False
    except OSError as ex:
        if ex.errno == 11:
            print('restarting container')
            os._exit(1) 
    except Exception as ex:
        print('[PARSE]',ex)
    finally:
        if 'client' in locals():
            try:    
                client.close_driver()
            except: pass
            try:    
                client.close_connection()
            except: pass
        time.sleep(0.2)
        if '_display' in locals():
            _display.stop()

def parse_thread():
    workers = settings.sets.count_thred        # желаемое число активных задач
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(parse, i == 0) for i in range(workers)}
        for i in range(workers):
            print(f'Thread {i} started')
            time.sleep(20)                      # ступенчатый запуск

        while True:
            # ждём, пока хоть один future завершится (успех или исключение)
            done, _ = wait(futures, return_when=FIRST_COMPLETED)

            for f in done:
                futures.remove(f)              # убираем старый
                if exc := f.exception():
                    print('[POOL EXCEPTION]', exc)

                # ставим новый parse-задачу
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
    time.sleep(30)
    try:
        if not settings.sets.debug:
            _display = Display(visible=False, size=(1920, 1080))
            _display.start()
        client = uc.Chrome(version_main=int(os.getenv('DRIVER_VERSION')))
    except Exception as ex:
        print('First start', ex)
    finally:
        if 'client' in locals():
            try:    
                client.close()
            except: pass
            try:    
                client.quit()
            except: pass
        if '_display' in locals():
            _display.stop()


if __name__ == "__main__":
    # check_db()
    # accounts()
    # parse()
    first_run()
    prepare_environment()
    parse_thread()



