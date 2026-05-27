# check_zeros.py
import sqlite3
import os

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "create_db", "data", "nutrition.db"
)

conn   = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT COUNT(*) FROM aliments WHERE calories_100g = 0
""")
print(f"Aliments avec calories = 0 : {cursor.fetchone()[0]}")

cursor.execute("""
    SELECT COUNT(*) FROM aliments WHERE calories_100g > 0
""")
print(f"Aliments avec calories > 0 : {cursor.fetchone()[0]}")

conn.close()
