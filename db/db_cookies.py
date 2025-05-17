import json
from db.core import Db


class DbCookies(Db):
    def __init__(self):
        super().__init__()

    def insert_data(self, cookies: dict) -> None:
        data = json.dumps(cookies)
        sql = f"INSERT INTO {self.table_cookies} (cookies) VALUES (%s)"
        self.insert(sql, (data,))

    def get_cookies(self) -> dict:
        sql = f"SELECT id, cookies FROM {self.table_cookies} WHERE status=0 and blocked=0 ORDER BY RAND() LIMIT 1"
        row = self.select(sql)
        if row:
            self.change_status(row[0][0], 1)
            return {
                'id': row[0][0],
                'cookies': json.loads(row[0][1])
            }
        return None
    
    def set_blocked(self, id: int) -> None:
        sql = f"UPDATE {self.table_cookies} SET blocked = 1 WHERE id = %s"
        self.insert(sql, (id, ))

    def change_status(self, id: int, status: int) -> None:
        sql = f"UPDATE {self.table_cookies} SET status = %s WHERE id = %s"
        self.insert(sql, (status, id))
        
