import sqlite3
from datetime import datetime

DATABASE_FILE = "finance_bot.db"


def create_command_logs_table():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS command_logs
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER,
                       username
                       TEXT,
                       full_name
                       TEXT,
                       command
                       TEXT,
                       timestamp
                       TEXT
                   )
                   """)
    conn.commit()
    conn.close()


def create_transactions_table():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS transactions
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER,
                       amount
                       REAL,
                       category
                       TEXT,
                       type
                       TEXT,
                       timestamp
                       TEXT
                   )
                   """)
    conn.commit()
    conn.close()


def create_budget_table():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS budget
                   (
                       user_id
                       INTEGER,
                       category
                       TEXT,
                       amount
                       REAL,
                       PRIMARY
                       KEY
                   (
                       user_id,
                       category
                   )
                       )
                   """)
    conn.commit()
    conn.close()


def create_budget_adjustments_table():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS budget_adjustments
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER,
                       category
                       TEXT,
                       amount
                       REAL,
                       timestamp
                       TEXT,
                       UNIQUE
                   (
                       user_id,
                       category
                   )
                       )
                   """)
    conn.commit()
    conn.close()


def create_goals_table():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS goals
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER,
                       amount
                       REAL,
                       description
                       TEXT,
                       date
                       TEXT
                   )
                   """)
    conn.commit()
    conn.close()


def create_piggy_bank_table():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS piggy_bank
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER,
                       name
                       TEXT,
                       target_amount
                       REAL,
                       current_amount
                       REAL
                       DEFAULT
                       0,
                       description
                       TEXT,
                       created_date
                       TEXT,
                       completed
                       INTEGER
                       DEFAULT
                       0
                   )
                   """)
    conn.commit()
    conn.close()


def create_debts_table():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS debts
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER,
                       debtor
                       TEXT,
                       amount
                       REAL,
                       status
                       TEXT
                       DEFAULT
                       'open',
                       due_date
                       TEXT,
                       creation_time
                       TEXT
                   )
                   """)
    conn.commit()
    conn.close()


def create_reminders_table():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS reminders
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER,
                       title
                       TEXT,
                       reminder_datetime
                       TEXT,
                       created_at
                       TEXT,
                       is_completed
                       INTEGER
                       DEFAULT
                       0
                   )
                   """)
    conn.commit()
    conn.close()


def init_database():
    create_command_logs_table()
    create_transactions_table()
    create_budget_table()
    create_budget_adjustments_table()
    create_goals_table()
    create_piggy_bank_table()
    create_debts_table()
    create_reminders_table()

    migrate_budget_data()
    migrate_debts_table()
    migrate_reminders_table()


def migrate_debts_table():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Check if the debts table exists
        cursor.execute("""
                       SELECT name
                       FROM sqlite_master
                       WHERE type = 'table'
                         AND name = 'debts'
                       """)

        if not cursor.fetchone():
            conn.close()
            return

        # Check if the creation_time column exists in the debts table
        cursor.execute("PRAGMA table_info(debts)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'creation_time' not in columns:
            print("Adding creation_time column to debts table")
            cursor.execute("ALTER TABLE debts ADD COLUMN creation_time TEXT")

            # Set a default value for existing records
            cursor.execute("UPDATE debts SET creation_time = ? WHERE creation_time IS NULL", 
                          (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))

            conn.commit()
            print("Migration of debts table completed successfully")

        conn.close()
    except Exception as e:
        print(f"Error migrating debts table: {e}")
        if 'conn' in locals():
            conn.close()


def migrate_reminders_table():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Check if the reminders table exists
        cursor.execute("""
                       SELECT name
                       FROM sqlite_master
                       WHERE type = 'table'
                         AND name = 'reminders'
                       """)

        if not cursor.fetchone():
            print("Creating reminders table")
            create_reminders_table()
            conn.close()
            return

        # Check if all required columns exist in the reminders table
        cursor.execute("PRAGMA table_info(reminders)")
        columns = [column[1] for column in cursor.fetchall()]

        required_columns = ['id', 'user_id', 'title', 'reminder_datetime', 'created_at', 'is_completed']
        missing_columns = [col for col in required_columns if col not in columns]

        if missing_columns:
            print(f"Adding missing columns to reminders table: {missing_columns}")
            for column in missing_columns:
                if column == 'is_completed':
                    cursor.execute(f"ALTER TABLE reminders ADD COLUMN {column} INTEGER DEFAULT 0")
                elif column == 'created_at':
                    cursor.execute(f"ALTER TABLE reminders ADD COLUMN {column} TEXT")
                    # Set a default value for existing records
                    cursor.execute("UPDATE reminders SET created_at = ? WHERE created_at IS NULL", 
                                  (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
                else:
                    cursor.execute(f"ALTER TABLE reminders ADD COLUMN {column} TEXT")

            conn.commit()
            print("Migration of reminders table completed successfully")

        conn.close()
    except Exception as e:
        print(f"Error migrating reminders table: {e}")
        if 'conn' in locals():
            conn.close()


def migrate_budget_data():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT name
                       FROM sqlite_master
                       WHERE type = 'table'
                         AND name = 'budget_adjustments'
                       """)

        if not cursor.fetchone():
            conn.close()
            return

        cursor.execute("""
                       SELECT DISTINCT user_id
                       FROM budget
                       """)

        users = cursor.fetchall()

        for (user_id,) in users:
            cursor.execute("""
                           SELECT category, amount
                           FROM budget
                           WHERE user_id = ?
                           """, (user_id,))

            budgets = cursor.fetchall()

            for category, budget_amount in budgets:
                cursor.execute("""
                               SELECT COALESCE(SUM(amount), 0)
                               FROM transactions
                               WHERE user_id = ?
                                 AND category = ?
                               """, (user_id, category))

                transaction_total = cursor.fetchone()[0]

                adjustment = budget_amount - transaction_total

                cursor.execute("""
                               SELECT id
                               FROM budget_adjustments
                               WHERE user_id = ?
                                 AND category = ?
                               """, (user_id, category))

                if not cursor.fetchone() and adjustment != 0:
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
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
                   INSERT INTO command_logs (user_id, username, full_name, command, timestamp)
                   VALUES (?, ?, ?, ?, ?)
                   """, (user_id, username, full_name, command, timestamp))
    conn.commit()
    conn.close()


def add_transaction(user_id, amount, category, transaction_type=None):
    if transaction_type is None:
        transaction_type = "дохід" if amount > 0 else "витрата"

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
        print(f"Помилка додавання транзакції: {e}")
        return False
    finally:
        conn.close()


def get_transaction_history(user_id, limit=10):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT timestamp, amount, category, type
                       FROM transactions
                       WHERE user_id = ?
                       ORDER BY timestamp DESC
                           LIMIT ?
                       """, (user_id, limit))
        transactions = cursor.fetchall()
        return transactions
    except Exception as e:
        print(f"Помилка отримання історії транзакцій: {e}")
        return []
    finally:
        conn.close()


def filter_transactions_by_category_or_type(user_id, filter_param, limit=20):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT timestamp, amount, category, type
                       FROM transactions
                       WHERE user_id = ? AND (LOWER (category) = LOWER (?) OR LOWER (type) = LOWER (?))
                       ORDER BY timestamp DESC
                           LIMIT ?
                       """, (user_id, filter_param, filter_param, limit))
        transactions = cursor.fetchall()
        return transactions
    except Exception as e:
        print(f"Помилка фільтрації транзакцій: {e}")
        return []
    finally:
        conn.close()


def get_last_transaction(user_id):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT id, amount, category, type, timestamp
                       FROM transactions
                       WHERE user_id = ?
                       ORDER BY timestamp DESC
                           LIMIT 1
                       """, (user_id,))
        transaction = cursor.fetchone()
        return transaction
    except Exception as e:
        print(f"Помилка отримання останньої транзакції: {e}")
        return None
    finally:
        conn.close()


def delete_transaction(transaction_id):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Помилка видалення транзакції: {e}")
        return False
    finally:
        conn.close()


def add_goal(user_id, amount, description):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
                       INSERT INTO goals (user_id, amount, description, date)
                       VALUES (?, ?, ?, date ('now'))
                       """, (user_id, amount, description))
        conn.commit()
        return True
    except Exception as e:
        print(f"Помилка додавання цілі: {e}")
        return False
    finally:
        conn.close()


def get_goals(user_id):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT amount, description, date
                       FROM goals
                       WHERE user_id = ?
                       ORDER BY date DESC
                       """, (user_id,))
        goals = cursor.fetchall()
        return goals
    except Exception as e:
        print(f"Помилка отримання цілей: {e}")
        return []
    finally:
        conn.close()


def set_budget(user_id, category, amount):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT COALESCE(SUM(amount), 0)
                       FROM transactions
                       WHERE user_id = ?
                         AND category = ?
                       """, (user_id, category))

        transaction_total = cursor.fetchone()[0]

        adjustment = amount - transaction_total

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
                       INSERT INTO budget_adjustments (user_id, category, amount, timestamp)
                       VALUES (?, ?, ?, ?) ON CONFLICT(user_id, category) DO
                       UPDATE SET amount = ?, timestamp = ?
                       """, (user_id, category, adjustment, timestamp, adjustment, timestamp))

        cursor.execute("""
                       INSERT INTO budget (user_id, category, amount)
                       VALUES (?, ?, ?) ON CONFLICT(user_id, category) DO
                       UPDATE SET amount = ?
                       """, (user_id, category, amount, amount))

        conn.commit()
        return True
    except Exception as e:
        print(f"Помилка встановлення бюджету: {e}")
        return False
    finally:
        conn.close()


def update_budget_for_transaction(user_id, amount, category):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT COALESCE(SUM(amount), 0)
                       FROM transactions
                       WHERE user_id = ?
                         AND category = ?
                       """, (user_id, category))

        transaction_total = cursor.fetchone()[0]

        cursor.execute("""
                       SELECT amount
                       FROM budget_adjustments
                       WHERE user_id = ?
                         AND category = ?
                       """, (user_id, category))

        adjustment_result = cursor.fetchone()
        adjustment = adjustment_result[0] if adjustment_result else 0

        new_budget = transaction_total + adjustment

        cursor.execute("""
                       SELECT amount
                       FROM budget
                       WHERE user_id = ?
                         AND category = ?
                       """, (user_id, category))

        result = cursor.fetchone()

        if result:
            cursor.execute("""
                           UPDATE budget
                           SET amount = ?
                           WHERE user_id = ?
                             AND category = ?
                           """, (new_budget, user_id, category))
        else:
            cursor.execute("""
                           INSERT INTO budget (user_id, category, amount)
                           VALUES (?, ?, ?)
                           """, (user_id, category, new_budget))

        conn.commit()
        return True
    except Exception as e:
        print(f"Помилка оновлення бюджету для транзакції: {e}")
        return False
    finally:
        conn.close()


def recalculate_user_budget(user_id):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM budget WHERE user_id = ?", (user_id,))

        cursor.execute("""
                       SELECT category, amount
                       FROM transactions
                       WHERE user_id = ?
                       """, (user_id,))

        transactions = cursor.fetchall()

        category_totals = {}
        for category, amount in transactions:
            if category in category_totals:
                category_totals[category] += amount
            else:
                category_totals[category] = amount

        cursor.execute("""
                       SELECT category, amount
                       FROM budget_adjustments
                       WHERE user_id = ?
                       """, (user_id,))

        adjustments = cursor.fetchall()

        for category, amount in adjustments:
            if category in category_totals:
                category_totals[category] += amount
            else:
                category_totals[category] = amount

        for category, total in category_totals.items():
            cursor.execute("""
                           INSERT INTO budget (user_id, category, amount)
                           VALUES (?, ?, ?)
                           """, (user_id, category, total))

        conn.commit()
        return True
    except Exception as e:
        print(f"Помилка перерахунку бюджету користувача: {e}")
        return False
    finally:
        conn.close()


def get_budgets(user_id):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT category, amount
                       FROM budget
                       WHERE user_id = ?
                       """, (user_id,))
        budgets = cursor.fetchall()
        return budgets
    except Exception as e:
        print(f"Помилка отримання бюджетів: {e}")
        return []
    finally:
        conn.close()


def check_database():
    try:
        import os
        if not os.path.exists(DATABASE_FILE):
            print(f"База даних {DATABASE_FILE} не існує")
            return False

        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"Існуючі таблиці: {tables}")

        if 'debts' not in tables:
            print("Таблиця 'debts' не існує, створюю її")
            create_debts_table()

        cursor.execute("PRAGMA table_info(debts)")
        columns = cursor.fetchall()
        print(f"Стовпці в таблиці debts: {columns}")

        if 'reminders' not in tables:
            print("Таблиця 'reminders' не існує, створюю її")
            create_reminders_table()

        cursor.execute("PRAGMA table_info(reminders)")
        columns = cursor.fetchall()
        print(f"Стовпці в таблиці reminders: {columns}")

        conn.close()
        return True
    except Exception as e:
        print(f"Помилка перевірки бази даних: {e}")
        return False


def save_debt(user_id, name, amount, due_date=None):
    if not check_database():
        print("Перевірка бази даних не вдалася, неможливо зберегти борг")
        return False

    try:
        if name is None or name.strip() == "":
            print("Помилка збереження боргу: Ім'я не може бути порожнім")
            return False

        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='debts'")
        if not cursor.fetchone():
            create_debts_table()

        query = """
                INSERT INTO debts (user_id, debtor, amount, status, due_date, creation_time)
                VALUES (?, ?, ?, 'open', ?, ?) \
                """
        due_date_value = due_date if due_date else datetime.now().strftime('%Y-%m-%d')
        creation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        params = (user_id, name, float(amount), due_date_value, creation_time)

        print(f"Виконання запиту: {query}")
        print(f"З параметрами: {params}")

        cursor.execute(query, params)

        row_id = cursor.lastrowid
        print(f"Вставлений ID рядка: {row_id}")

        conn.commit()
        return True
    except sqlite3.Error as sql_error:
        print(f"SQLite помилка збереження боргу: {sql_error}")
        return False
    except Exception as e:
        print(f"Помилка збереження боргу: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def get_active_debts(user_id):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT debtor, amount, due_date, creation_time
                       FROM debts
                       WHERE user_id = ?
                         AND status = 'open'
                       """, (user_id,))
        debts = cursor.fetchall()
        return debts
    except Exception as e:
        print(f"Помилка отримання активних боргів: {e}")
        return []
    finally:
        conn.close()


def get_debt_history(user_id):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT debtor, amount, status, due_date, creation_time
                       FROM debts
                       WHERE user_id = ?
                       ORDER BY due_date DESC
                       """, (user_id,))
        debts = cursor.fetchall()
        return debts
    except Exception as e:
        print(f"Помилка отримання історії боргів: {e}")
        return []
    finally:
        conn.close()


def close_debt(user_id, name, amount=None):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        if amount is not None:
            cursor.execute("""
                           UPDATE debts
                           SET status = 'closed'
                           WHERE user_id = ?
                             AND debtor = ?
                             AND amount = ?
                             AND status = 'open'
                           """, (user_id, name, float(amount)))
        else:
            cursor.execute("""
                           UPDATE debts
                           SET status = 'closed'
                           WHERE user_id = ?
                             AND debtor = ?
                             AND status = 'open'
                           """, (user_id, name))

        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Помилка закриття боргу: {e}")
        return False
    finally:
        conn.close()


def add_piggy_bank_goal(user_id, name, target_amount, description=""):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
                       INSERT INTO piggy_bank (user_id, name, target_amount, current_amount, description, created_date,
                                               completed)
                       VALUES (?, ?, ?, 0, ?, ?, 0)
                       """, (user_id, name, float(target_amount), description, created_date))

        conn.commit()
        return True
    except Exception as e:
        print(f"Помилка додавання цілі скарбнички: {e}")
        return False
    finally:
        conn.close()


def get_piggy_bank_goals(user_id):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT id, name, target_amount, current_amount, description, created_date, completed
                       FROM piggy_bank
                       WHERE user_id = ?
                       ORDER BY created_date DESC
                       """, (user_id,))
        goals = cursor.fetchall()
        return goals
    except Exception as e:
        print(f"Помилка отримання цілей скарбнички: {e}")
        return []
    finally:
        conn.close()


def add_funds_to_goal(user_id, goal_id, amount):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT current_amount, target_amount, completed
                       FROM piggy_bank
                       WHERE id = ?
                         AND user_id = ?
                       """, (goal_id, user_id))

        result = cursor.fetchone()
        if not result:
            return False

        current_amount, target_amount, completed = result

        if completed:
            return False

        cursor.execute("""
                       SELECT COALESCE(SUM(amount), 0)
                       FROM budget
                       WHERE user_id = ?
                       """, (user_id,))

        total_budget = cursor.fetchone()[0]

        if total_budget < amount:
            return False

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
                       INSERT INTO transactions (user_id, amount, category, type, timestamp)
                       VALUES (?, ?, ?, ?, ?)
                       """, (user_id, -amount, "Скарбничка", "витрата", timestamp))

        cursor.execute("""
                       SELECT COALESCE(SUM(amount), 0)
                       FROM transactions
                       WHERE user_id = ?
                         AND category = ?
                       """, (user_id, "Скарбничка"))

        transaction_total = cursor.fetchone()[0]

        cursor.execute("""
                       SELECT amount
                       FROM budget_adjustments
                       WHERE user_id = ?
                         AND category = ?
                       """, (user_id, "Скарбничка"))

        adjustment_result = cursor.fetchone()
        adjustment = adjustment_result[0] if adjustment_result else 0

        new_budget = transaction_total + adjustment

        cursor.execute("""
                       SELECT amount
                       FROM budget
                       WHERE user_id = ?
                         AND category = ?
                       """, (user_id, "Скарбничка"))

        result = cursor.fetchone()

        if result:
            cursor.execute("""
                           UPDATE budget
                           SET amount = ?
                           WHERE user_id = ?
                             AND category = ?
                           """, (new_budget, user_id, "Скарбничка"))
        else:
            cursor.execute("""
                           INSERT INTO budget (user_id, category, amount)
                           VALUES (?, ?, ?)
                           """, (user_id, "Скарбничка", new_budget))

        new_amount = current_amount + float(amount)

        new_completed = 1 if new_amount >= target_amount else 0

        cursor.execute("""
                       UPDATE piggy_bank
                       SET current_amount = ?,
                           completed      = ?
                       WHERE id = ?
                         AND user_id = ?
                       """, (new_amount, new_completed, goal_id, user_id))

        conn.commit()
        return True
    except Exception as e:
        print(f"Помилка додавання коштів до цілі: {e}")
        return False
    finally:
        conn.close()


def delete_piggy_bank_goal(user_id, goal_id):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute("""
                       DELETE
                       FROM piggy_bank
                       WHERE id = ?
                         AND user_id = ?
                       """, (goal_id, user_id))

        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Помилка видалення цілі скарбнички: {e}")
        return False
    finally:
        conn.close()


def get_piggy_bank_goal(user_id, goal_id):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT id, name, target_amount, current_amount, description, created_date, completed
                       FROM piggy_bank
                       WHERE id = ?
                         AND user_id = ?
                       """, (goal_id, user_id))
        goal = cursor.fetchone()
        return goal
    except Exception as e:
        print(f"Помилка отримання цілі скарбнички: {e}")
        return None
    finally:
        conn.close()


def add_reminder(user_id, title, reminder_datetime):
    if not check_database():
        print("Перевірка бази даних не вдалася, неможливо додати нагадування")
        return None

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reminders'")
        if not cursor.fetchone():
            create_reminders_table()

        cursor.execute("""
                       INSERT INTO reminders (user_id, title, reminder_datetime, created_at, is_completed)
                       VALUES (?, ?, ?, ?, 0)
                       """, (user_id, title, reminder_datetime, created_at))

        reminder_id = cursor.lastrowid
        conn.commit()
        print(f"Додано нагадування з ID: {reminder_id}")
        return reminder_id
    except Exception as e:
        print(f"Помилка додавання нагадування: {e}")
        return None
    finally:
        conn.close()


def get_reminders(user_id, include_completed=False):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        if include_completed:
            cursor.execute("""
                           SELECT id, title, reminder_datetime, created_at, is_completed
                           FROM reminders
                           WHERE user_id = ?
                           ORDER BY reminder_datetime
                           """, (user_id,))
        else:
            cursor.execute("""
                           SELECT id, title, reminder_datetime, created_at, is_completed
                           FROM reminders
                           WHERE user_id = ?
                             AND is_completed = 0
                           ORDER BY reminder_datetime
                           """, (user_id,))

        reminders = cursor.fetchall()
        return reminders
    except Exception as e:
        print(f"Помилка отримання нагадувань: {e}")
        return []
    finally:
        conn.close()


def get_reminder(user_id, reminder_id):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT id, title, reminder_datetime, created_at, is_completed
                       FROM reminders
                       WHERE id = ?
                         AND user_id = ?
                       """, (reminder_id, user_id))
        reminder = cursor.fetchone()
        return reminder
    except Exception as e:
        print(f"Помилка отримання нагадування: {e}")
        return None
    finally:
        conn.close()


def update_reminder(user_id, reminder_id, title=None, reminder_datetime=None):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT title, reminder_datetime
                       FROM reminders
                       WHERE id = ?
                         AND user_id = ?
                       """, (reminder_id, user_id))

        current_data = cursor.fetchone()
        if not current_data:
            return False

        current_title, current_datetime = current_data

        new_title = title if title is not None else current_title
        new_datetime = reminder_datetime if reminder_datetime is not None else current_datetime

        cursor.execute("""
                       UPDATE reminders
                       SET title             = ?,
                           reminder_datetime = ?
                       WHERE id = ?
                         AND user_id = ?
                       """, (new_title, new_datetime, reminder_id, user_id))

        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Помилка оновлення нагадування: {e}")
        return False
    finally:
        conn.close()


def mark_reminder_completed(user_id, reminder_id):
    if not check_database():
        print("Перевірка бази даних не вдалася, неможливо позначити нагадування як виконане")
        return False

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reminders'")
        if not cursor.fetchone():
            print("Таблиця 'reminders' не існує, створюю її")
            create_reminders_table()
            conn.close()
            return False

        cursor.execute("""
                       UPDATE reminders
                       SET is_completed = 1
                       WHERE id = ?
                         AND user_id = ?
                       """, (reminder_id, user_id))

        conn.commit()
        rows_affected = cursor.rowcount
        print(f"Позначено {rows_affected} нагадувань як виконані")
        return rows_affected > 0
    except Exception as e:
        print(f"Помилка позначення нагадування як виконаного: {e}")
        return False
    finally:
        conn.close()


def delete_reminder(user_id, reminder_id):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute("""
                       DELETE
                       FROM reminders
                       WHERE id = ?
                         AND user_id = ?
                       """, (reminder_id, user_id))

        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting reminder: {e}")
        return False
    finally:
        conn.close()


def get_due_reminders():
    if not check_database():
        print("Перевірка бази даних не вдалася, неможливо отримати нагадування")
        return []

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reminders'")
        if not cursor.fetchone():
            print("Таблиця 'reminders' не існує, створюю її")
            create_reminders_table()
            conn.close()
            return []

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Поточний час: {current_time}")

        cursor.execute("""
                       SELECT id, user_id, title, reminder_datetime
                       FROM reminders
                       WHERE reminder_datetime <= ?
                         AND is_completed = 0
                       """, (current_time,))

        reminders = cursor.fetchall()
        print(f"Знайдено {len(reminders)} нагадувань для відправки")
        for reminder in reminders:
            print(f"Нагадування: {reminder}")
        return reminders
    except Exception as e:
        print(f"Помилка отримання нагадувань: {e}")
        return []
    finally:
        conn.close()
