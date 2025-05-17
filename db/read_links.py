import mysql.connector
import csv
from tqdm import tqdm  


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "opencorporates"
}

FILE_PATH = "urls.tsv" 


conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

total_lines = sum(1 for _ in open(FILE_PATH, "r"))
print(f"Всего строк в файле: {total_lines}")

with open(FILE_PATH, "r", encoding="utf-8") as file:
    reader = csv.reader(file, delimiter="\t") 

    batch_size = 10000  
    batch = []

    for row in tqdm(reader, total=total_lines, desc="Загрузка в MySQL"):
        if not row:  
            continue
        
        url = row[0]  
        batch.append((url,))

        if len(batch) >= batch_size:
            cursor.executemany("INSERT IGNORE INTO companies (url) VALUES (%s)", batch)
            conn.commit()
            batch = []

    if batch:
        cursor.executemany("INSERT IGNORE INTO companies (url) VALUES (%s)", batch)
        conn.commit()

cursor.close()
conn.close()

print("✅ Все данные загружены в MySQL!")