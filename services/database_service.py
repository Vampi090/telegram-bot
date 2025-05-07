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


def create_budget_adjustments_table():
    """Создает таблицу корректировок бюджета в базе данных (если она еще не существует)."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget_adjustments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            amount REAL,
            timestamp TEXT,
            UNIQUE(user_id, category)
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
            debtor TEXT,
            amount REAL,
            status TEXT DEFAULT 'open',
            due_date TEXT
        )
    """)
    conn.commit()
    conn.close()


def init_database():
    """Инициализирует все необходимые таблицы в базе данных."""
    create_command_logs_table()
    create_transactions_table()
    create_budget_table()
    create_budget_adjustments_table()
    create_goals_table()
    create_debts_table()

    # Миграция существующих данных бюджета
    migrate_budget_data()


def migrate_budget_data():
    """
    Мигрирует существующие данные бюджета в новую схему.
    Вычисляет корректировки бюджета на основе разницы между текущим бюджетом и суммой транзакций.
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Проверяем, существует ли таблица budget_adjustments
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='budget_adjustments'
        """)

        if not cursor.fetchone():
            # Таблица еще не создана, пропускаем миграцию
            conn.close()
            return

        # Получаем всех пользователей с бюджетами
        cursor.execute("""
            SELECT DISTINCT user_id FROM budget
        """)

        users = cursor.fetchall()

        for (user_id,) in users:
            # Получаем все категории бюджета для пользователя
            cursor.execute("""
                SELECT category, amount FROM budget
                WHERE user_id = ?
            """, (user_id,))

            budgets = cursor.fetchall()

            for category, budget_amount in budgets:
                # Получаем сумму транзакций для этой категории
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM transactions
                    WHERE user_id = ? AND category = ?
                """, (user_id, category))

                transaction_total = cursor.fetchone()[0]

                # Вычисляем корректировку как разницу между бюджетом и суммой транзакций
                adjustment = budget_amount - transaction_total

                # Проверяем, существует ли уже корректировка для этой категории
                cursor.execute("""
                    SELECT id FROM budget_adjustments
                    WHERE user_id = ? AND category = ?
                """, (user_id, category))

                if not cursor.fetchone() and adjustment != 0:
                    # Если корректировки нет и она не равна нулю, создаем новую
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("""
                        INSERT INTO budget_adjustments (user_id, category, amount, timestamp)
                        VALUES (?, ?, ?, ?)
                    """, (user_id, category, adjustment, timestamp))

        conn.commit()
    except Exception as e:
        print(f"Error migrating budget data: {e}")
    finally:
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
    Устанавливает бюджет для категории и сохраняет корректировку бюджета.

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

        # Получаем текущий бюджет на основе транзакций
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE user_id = ? AND category = ?
        """, (user_id, category))

        transaction_total = cursor.fetchone()[0]

        # Вычисляем корректировку как разницу между желаемым бюджетом и суммой транзакций
        adjustment = amount - transaction_total

        # Сохраняем корректировку в таблице budget_adjustments
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO budget_adjustments (user_id, category, amount, timestamp)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, category) DO UPDATE SET amount = ?, timestamp = ?
        """, (user_id, category, adjustment, timestamp, adjustment, timestamp))

        # Устанавливаем общий бюджет
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


def update_budget_for_transaction(user_id, amount, category):
    """
    Обновляет бюджет пользователя на основе транзакции.
    Если бюджет для категории не существует, он будет создан.
    Сохраняет существующие корректировки бюджета.

    Args:
        user_id (int): ID пользователя
        amount (float): Сумма транзакции (положительная для дохода, отрицательная для расхода)
        category (str): Категория транзакции

    Returns:
        bool: True если бюджет успешно обновлен, иначе False
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Получаем сумму транзакций для данной категории
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE user_id = ? AND category = ?
        """, (user_id, category))

        transaction_total = cursor.fetchone()[0]

        # Получаем корректировку бюджета, если она существует
        cursor.execute("""
            SELECT amount FROM budget_adjustments
            WHERE user_id = ? AND category = ?
        """, (user_id, category))

        adjustment_result = cursor.fetchone()
        adjustment = adjustment_result[0] if adjustment_result else 0

        # Вычисляем новый общий бюджет
        new_budget = transaction_total + adjustment

        # Проверяем, существует ли бюджет для данной категории
        cursor.execute("""
            SELECT amount FROM budget
            WHERE user_id = ? AND category = ?
        """, (user_id, category))

        result = cursor.fetchone()

        if result:
            # Бюджет существует, обновляем его
            cursor.execute("""
                UPDATE budget
                SET amount = ?
                WHERE user_id = ? AND category = ?
            """, (new_budget, user_id, category))
        else:
            # Бюджет не существует, создаем новый
            cursor.execute("""
                INSERT INTO budget (user_id, category, amount)
                VALUES (?, ?, ?)
            """, (user_id, category, new_budget))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating budget for transaction: {e}")
        return False
    finally:
        conn.close()


def recalculate_user_budget(user_id):
    """
    Пересчитывает весь бюджет пользователя на основе всех его транзакций и корректировок.
    Это полезно для синхронизации бюджета с транзакциями и сохранения пользовательских корректировок.

    Args:
        user_id (int): ID пользователя

    Returns:
        bool: True если бюджет успешно пересчитан, иначе False
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Сначала очищаем текущий бюджет пользователя
        cursor.execute("DELETE FROM budget WHERE user_id = ?", (user_id,))

        # Получаем все транзакции пользователя
        cursor.execute("""
            SELECT category, amount FROM transactions
            WHERE user_id = ?
        """, (user_id,))

        transactions = cursor.fetchall()

        # Группируем транзакции по категориям и суммируем
        category_totals = {}
        for category, amount in transactions:
            if category in category_totals:
                category_totals[category] += amount
            else:
                category_totals[category] = amount

        # Получаем все корректировки бюджета пользователя
        cursor.execute("""
            SELECT category, amount FROM budget_adjustments
            WHERE user_id = ?
        """, (user_id,))

        adjustments = cursor.fetchall()

        # Добавляем корректировки к суммам транзакций
        for category, amount in adjustments:
            if category in category_totals:
                category_totals[category] += amount
            else:
                category_totals[category] = amount

        # Создаем новые записи бюджета
        for category, total in category_totals.items():
            cursor.execute("""
                INSERT INTO budget (user_id, category, amount)
                VALUES (?, ?, ?)
            """, (user_id, category, total))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error recalculating user budget: {e}")
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
def check_database():
    """
    Проверяет состояние базы данных и наличие необходимых таблиц.

    Returns:
        bool: True если база данных в порядке, иначе False
    """
    try:
        # Проверяем, существует ли файл базы данных
        import os
        if not os.path.exists(DATABASE_FILE):
            print(f"Database file {DATABASE_FILE} does not exist")
            return False

        # Проверяем, можем ли мы подключиться к базе данных
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Проверяем, существуют ли необходимые таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"Existing tables: {tables}")

        if 'debts' not in tables:
            print("Table 'debts' does not exist, creating it")
            create_debts_table()

        # Проверяем структуру таблицы debts
        cursor.execute("PRAGMA table_info(debts)")
        columns = cursor.fetchall()
        print(f"Columns in debts table: {columns}")

        conn.close()
        return True
    except Exception as e:
        print(f"Error checking database: {e}")
        return False


def save_debt(user_id, name, amount):
    """
    Добавляет новый долг в базу данных.

    Args:
        user_id (int): ID пользователя
        name (str): Имя должника или кредитора (значение поля debtor)
        amount (float): Сумма долга

    Returns:
        bool: True если долг успешно добавлен, иначе False
    """
    # Проверяем состояние базы данных
    if not check_database():
        print("Database check failed, cannot save debt")
        return False

    try:
        # Проверяем входные данные
        if name is None or name.strip() == "":
            print("Error saving debt: Name cannot be empty")
            return False

        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Проверяем, существует ли таблица debts
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='debts'")
        if not cursor.fetchone():
            # Таблица не существует, создаем ее
            create_debts_table()

        # Подготавливаем данные для вставки
        query = """
            INSERT INTO debts (user_id, debtor, amount, status, due_date)
            VALUES (?, ?, ?, 'open', datetime('now'))
        """
        params = (user_id, name, float(amount))

        print(f"Executing query: {query}")
        print(f"With parameters: {params}")

        # Вставляем данные
        cursor.execute(query, params)

        # Проверяем, что запись была добавлена
        row_id = cursor.lastrowid
        print(f"Inserted row ID: {row_id}")

        conn.commit()
        return True
    except sqlite3.Error as sql_error:
        print(f"SQLite error saving debt: {sql_error}")
        return False
    except Exception as e:
        print(f"Error saving debt: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def get_active_debts(user_id):
    """
    Получает список активных долгов пользователя.

    Args:
        user_id (int): ID пользователя

    Returns:
        list: Список активных долгов в формате (debtor, amount)
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT debtor, amount FROM debts
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
        list: Список всех долгов в формате (debtor, amount, status, due_date)
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT debtor, amount, status, due_date FROM debts
            WHERE user_id = ?
            ORDER BY due_date DESC
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
        name (str): Имя должника или кредитора (значение поля debtor)
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
                WHERE user_id = ? AND debtor = ? AND amount = ? AND status = 'open'
            """, (user_id, name, float(amount)))
        else:
            cursor.execute("""
                UPDATE debts
                SET status = 'closed'
                WHERE user_id = ? AND debtor = ? AND status = 'open'
            """, (user_id, name))

        conn.commit()
        return cursor.rowcount > 0  # Возвращаем True, если хотя бы одна строка была обновлена
    except Exception as e:
        print(f"Error closing debt: {e}")
        return False
    finally:
        conn.close()
