import sqlite3
from datetime import datetime

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


def create_transactions_table():
    """Создает таблицу транзакций в базе данных (если она еще не существует)."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            category TEXT,
            type TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


def create_budget_table():
    """Создает таблицу бюджетов в базе данных (если она еще не существует)."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            user_id INTEGER,
            category TEXT,
            amount REAL,
            PRIMARY KEY (user_id, category)
        )
    """)
    conn.commit()
    conn.close()


def create_goals_table():
    """Создает таблицу целей в базе данных (если она еще не существует)."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            description TEXT,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()


def create_debts_table():
    """Создает таблицу долгов в базе данных (если она еще не существует)."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            amount REAL,
            status TEXT DEFAULT 'open',
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


def init_database():
    """Инициализирует все необходимые таблицы в базе данных."""
    create_command_logs_table()
    create_transactions_table()
    create_budget_table()
    create_goals_table()
    create_debts_table()


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


# Функции для работы с транзакциями
def add_transaction(user_id, amount, category, transaction_type=None):
    """
    Добавляет новую транзакцию в базу данных.

    Args:
        user_id (int): ID пользователя
        amount (float): Сумма транзакции
        category (str): Категория транзакции
        transaction_type (str, optional): Тип транзакции. Если не указан, определяется автоматически.

    Returns:
        bool: True если транзакция успешно добавлена, иначе False
    """
    if transaction_type is None:
        transaction_type = "доход" if amount > 0 else "расход"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (user_id, amount, category, type, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, amount, category, transaction_type, timestamp))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding transaction: {e}")
        return False
    finally:
        conn.close()


def get_transaction_history(user_id, limit=10):
    """
    Получает историю транзакций пользователя.

    Args:
        user_id (int): ID пользователя
        limit (int, optional): Максимальное количество транзакций. По умолчанию 10.

    Returns:
        list: Список транзакций в формате (timestamp, amount, category, type)
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, amount, category, type FROM transactions
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))
        transactions = cursor.fetchall()
        return transactions
    except Exception as e:
        print(f"Error getting transaction history: {e}")
        return []
    finally:
        conn.close()


def filter_transactions_by_category_or_type(user_id, filter_param, limit=20):
    """
    Фильтрует транзакции по категории или типу.

    Args:
        user_id (int): ID пользователя
        filter_param (str): Параметр фильтрации (категория или тип)
        limit (int, optional): Максимальное количество транзакций. По умолчанию 20.

    Returns:
        list: Отфильтрованный список транзакций
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, amount, category, type FROM transactions
            WHERE user_id = ? AND (LOWER(category) = LOWER(?) OR LOWER(type) = LOWER(?))
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, filter_param, filter_param, limit))
        transactions = cursor.fetchall()
        return transactions
    except Exception as e:
        print(f"Error filtering transactions: {e}")
        return []
    finally:
        conn.close()


def get_last_transaction(user_id):
    """
    Получает последнюю транзакцию пользователя.

    Args:
        user_id (int): ID пользователя

    Returns:
        tuple: Данные последней транзакции или None, если транзакций нет
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, amount, category, type, timestamp FROM transactions
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (user_id,))
        transaction = cursor.fetchone()
        return transaction
    except Exception as e:
        print(f"Error getting last transaction: {e}")
        return None
    finally:
        conn.close()


def delete_transaction(transaction_id):
    """
    Удаляет транзакцию по ID.

    Args:
        transaction_id (int): ID транзакции для удаления

    Returns:
        bool: True если транзакция успешно удалена, иначе False
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting transaction: {e}")
        return False
    finally:
        conn.close()


# Функции для работы с целями
def add_goal(user_id, amount, description):
    """
    Добавляет новую финансовую цель в базу данных.

    Args:
        user_id (int): ID пользователя
        amount (float): Сумма цели
        description (str): Описание цели

    Returns:
        bool: True если цель успешно добавлена, иначе False
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO goals (user_id, amount, description, date)
            VALUES (?, ?, ?, date('now'))
        """, (user_id, amount, description))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding goal: {e}")
        return False
    finally:
        conn.close()


def get_goals(user_id):
    """
    Получает список целей пользователя.

    Args:
        user_id (int): ID пользователя

    Returns:
        list: Список целей в формате (amount, description, date)
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT amount, description, date FROM goals
            WHERE user_id = ?
            ORDER BY date DESC
        """, (user_id,))
        goals = cursor.fetchall()
        return goals
    except Exception as e:
        print(f"Error getting goals: {e}")
        return []
    finally:
        conn.close()


# Функции для работы с бюджетом
def set_budget(user_id, category, amount):
    """
    Устанавливает бюджет для категории.

    Args:
        user_id (int): ID пользователя
        category (str): Категория бюджета
        amount (float): Сумма бюджета

    Returns:
        bool: True если бюджет успешно установлен, иначе False
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO budget (user_id, category, amount)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, category) DO UPDATE SET amount = ?
        """, (user_id, category, amount, amount))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error setting budget: {e}")
        return False
    finally:
        conn.close()


def get_budgets(user_id):
    """
    Получает список бюджетов пользователя.

    Args:
        user_id (int): ID пользователя

    Returns:
        list: Список бюджетов в формате (category, amount)
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, amount FROM budget
            WHERE user_id = ?
        """, (user_id,))
        budgets = cursor.fetchall()
        return budgets
    except Exception as e:
        print(f"Error getting budgets: {e}")
        return []
    finally:
        conn.close()


# Функции для работы с долгами
def save_debt(user_id, name, amount):
    """
    Добавляет новый долг в базу данных.

    Args:
        user_id (int): ID пользователя
        name (str): Имя должника или кредитора
        amount (float): Сумма долга

    Returns:
        bool: True если долг успешно добавлен, иначе False
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO debts (user_id, name, amount, status, timestamp)
            VALUES (?, ?, ?, 'open', datetime('now'))
        """, (user_id, name, float(amount)))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving debt: {e}")
        return False
    finally:
        conn.close()


def get_active_debts(user_id):
    """
    Получает список активных долгов пользователя.

    Args:
        user_id (int): ID пользователя

    Returns:
        list: Список активных долгов в формате (name, amount)
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, amount FROM debts
            WHERE user_id = ? AND status = 'open'
        """, (user_id,))
        debts = cursor.fetchall()
        return debts
    except Exception as e:
        print(f"Error getting active debts: {e}")
        return []
    finally:
        conn.close()


def get_debt_history(user_id):
    """
    Получает историю долгов пользователя.

    Args:
        user_id (int): ID пользователя

    Returns:
        list: Список всех долгов в формате (name, amount, status, timestamp)
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, amount, status, timestamp FROM debts
            WHERE user_id = ?
            ORDER BY timestamp DESC
        """, (user_id,))
        debts = cursor.fetchall()
        return debts
    except Exception as e:
        print(f"Error getting debt history: {e}")
        return []
    finally:
        conn.close()


def close_debt(user_id, name, amount=None):
    """
    Закрывает долг пользователя.

    Args:
        user_id (int): ID пользователя
        name (str): Имя должника или кредитора
        amount (float, optional): Сумма долга. Если не указана, закрываются все долги с указанным именем.

    Returns:
        bool: True если долг успешно закрыт, иначе False
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        if amount is not None:
            cursor.execute("""
                UPDATE debts
                SET status = 'closed'
                WHERE user_id = ? AND name = ? AND amount = ? AND status = 'open'
            """, (user_id, name, float(amount)))
        else:
            cursor.execute("""
                UPDATE debts
                SET status = 'closed'
                WHERE user_id = ? AND name = ? AND status = 'open'
            """, (user_id, name))

        conn.commit()
        return cursor.rowcount > 0  # Возвращаем True, если хотя бы одна строка была обновлена
    except Exception as e:
        print(f"Error closing debt: {e}")
        return False
    finally:
        conn.close()
