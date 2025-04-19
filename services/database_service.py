import sqlite3

DATABASE_FILE = "finance_bot.db"


def create_command_logs_table():
    """Создает таблицу логов в базе данных (если она еще не существует)."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS command_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            command TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


def insert_command_log(user_id, username, full_name, command, timestamp):
    """Вставляет запись в таблицу логов."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO command_logs (user_id, username, full_name, command, timestamp) 
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, username, full_name, command, timestamp))
    conn.commit()
    conn.close()
