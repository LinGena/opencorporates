from accounts.create import CreateAccount
from db.core import IsDbCreated, IsDbTable
import warnings
import time
from threading import Thread
from scraper.scraper import Scraper
from config.settings import settings


warnings.filterwarnings('ignore', message='Unverified HTTPS request')


def accounts():
    for i in range(0, 300):
        CreateAccount().create_account_cookies()


def parse(first_start: bool = False):
    while True:
        try:
            # url = ['https://opencorporates.com/companies/us_ca/0806592']
            # Scraper().run(url)
            Scraper(first_start).run()
        except Exception as ex:
            print(ex)

def parse_thread():
    first_start = True
    for i in range(settings.sets.count_thred):
        t = Thread(target=parse, args=(first_start,))
        t.start()
        print(f'Thread {i} started')
        first_start = False
        time.sleep(30)


def check_db():
    IsDbCreated().check()
    IsDbTable().check()

if __name__ == "__main__":
    # check_db()
    # accounts()
    # parse()
    parse_thread()



