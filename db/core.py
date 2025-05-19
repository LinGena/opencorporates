from mysql.connector import connect, Error
import time
from config.settings import settings
from utils.logger import Logger


class Db():
    def __init__(self):
        self.logger = Logger().get_logger(__name__)
        self.connecting()
        self.table_companies = settings.db.table_companies
        self.table_cookies = settings.db.table_cookies
        

    def connecting(self, max_retries=10, delay=5) -> None:    
        for attempt in range(max_retries):
            try:
                self.connection = connect(
                    host=settings.db.db_host,
                    port=settings.db.db_port,
                    user=settings.db.db_user,
                    password=settings.db.db_password,
                    database=settings.db.db_database
                )
                self.cursor = self.connection.cursor()
                return 
            except Error as e:
                self.logger.error(f"Connection failed: {e}")
                time.sleep(delay)
        raise Exception("Could not connect to the database after multiple attempts")

    def __del__(self):
        self.close_connection()

    def insert(self, sql: str, params: tuple = None) -> None:
        if not params:
            self.cursor.execute(sql)
        else:
            self.cursor.execute(sql, params)
        self.connection.commit()

    def select(self, sql: str) -> list:
        self.cursor.execute(sql)
        rows = self.cursor.fetchall() 
        return rows
        
    def close_connection(self) -> None:
        if hasattr(self, 'connection'):
            self.connection.close()


class IsDbCreated():
    def check(self) -> None:
        for attempt in range(5):
            try:
                connection = connect(host=settings.db.db_host, 
                                     port=settings.db.db_port, 
                                     user=settings.db.db_user, 
                                     password=settings.db.db_password)
                cursor = connection.cursor()
                cursor.execute("SET GLOBAL sql_mode=(SELECT REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', ''))")
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.db.db_database}")
                connection.close()
                IsDbTable().check()
                return
            except Error as e:
                print(f"Connection failed: {e}")
                time.sleep(5)
        raise Exception("Could not connect to MySQL for database creation after multiple attempts.")


class IsDbTable(Db):
    def __init__(self):
        super().__init__()

    def check(self) -> None:
        if self.check_tables(self.table_companies):
            self.create_companies()
        if self.check_tables(self.table_cookies):
            self.create_cookies()

    def create_companies(self) -> None:
        self.insert(f"""
            CREATE TABLE `{self.table_companies}` (
                `id` BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                `url` VARCHAR(255) NOT NULL UNIQUE,
                `datas` JSON DEFAULT NULL,
                `status` INT DEFAULT 1
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """)
    
    def create_cookies(self) -> None:
        self.insert(f"""
            CREATE TABLE `{self.table_cookies}` (
                `id` BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                `cookies` JSON NOT NULL,
                `status` INT DEFAULT 0,
                `blocked` INT DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """)
    
    def check_tables(self, table_name: str) -> bool:
        sql = f"SHOW TABLES FROM {settings.db.db_database} LIKE '{table_name}'"
        rows = self.select(sql)
        if len(rows) == 0:
            return True
        return False