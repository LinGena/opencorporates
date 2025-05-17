import json
from db.core import Db


class DbCompanies(Db):
    def __init__(self):
        super().__init__()

    def get_urls(self, count_urls: int = 300, urls: list = None) -> list:
        if not urls:
            sql = f"SELECT id, url FROM {self.table_companies} WHERE status=1 LIMIT {count_urls} FOR UPDATE SKIP LOCKED"
        else:
            escaped_urls = ','.join(f"'{url}'" for url in urls)
            sql = f"SELECT id, url FROM {self.table_companies} WHERE status=1 AND url IN ({escaped_urls}) LIMIT {count_urls} FOR UPDATE SKIP LOCKED"
        rows = self.select(sql)
        if rows:
            ids = [str(row[0]) for row in rows]
            ids_str = ','.join(ids)
            update_sql = f"UPDATE {self.table_companies} SET status=2 WHERE id IN ({ids_str})"
            self.insert(update_sql)
        return rows
    
    def update_status(self, id: int, status: int = 400) -> None:
        sql = f"UPDATE {self.table_companies} SET status = %s WHERE id = %s"
        self.insert(sql, (status, id))

    def update_datas(self, id: int, result: dict) -> None:
        datas = json.dumps(result)
        sql = f"UPDATE {self.table_companies} SET datas = %s, status = 200 WHERE id = %s"
        self.insert(sql, (datas, id))

    def get_results_data(self) -> list:
        sql = f"SELECT datas FROM {self.table_companies} WHERE status!=1 LIMIT 1000"
        rows = self.select(sql)
        return rows
    
    def check_urls_in_table(self, urls: list) -> list:
        for url in urls:
            sql = f"SELECT url FROM {self.table_companies} WHERE url='{url}' LIMIT 1"
            rows = self.select(sql)
            if not rows:
                sql = f"INSERT INTO {self.table_companies} (url) VALUES ('{url}')"
                self.insert(sql)
                print(f"Inserted URL: {url}")
