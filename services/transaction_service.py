import sqlite3
from models.transaction import Transaction
from services.database_service import (
    add_transaction as db_add_transaction,
    get_transaction_history as db_get_transaction_history,
    filter_transactions_by_category_or_type as db_filter_transactions,
    get_last_transaction as db_get_last_transaction,
    delete_transaction as db_delete_transaction,
    update_budget_for_transaction as db_update_budget,
    recalculate_user_budget as db_recalculate_budget
)


def add_new_transaction(user_id, amount, category, transaction_type=None):
    """
    Добавляет новую транзакцию.

    Args:
        user_id (int): ID пользователя
        amount (float): Сумма транзакции
        category (str): Категория транзакции
        transaction_type (str, optional): Тип транзакции

    Returns:
        Transaction: Объект добавленной транзакции или None в случае ошибки
    """
    # Создаем объект транзакции
    transaction = Transaction(
        user_id=user_id,
        amount=amount,
        category=category,
        transaction_type=transaction_type
    )

    # Добавляем в базу данных
    success = db_add_transaction(
        user_id=transaction.user_id,
        amount=transaction.amount,
        category=transaction.category,
        transaction_type=transaction.transaction_type
    )

    if success:
        # Обновляем бюджет пользователя
        db_update_budget(
            user_id=transaction.user_id,
            amount=transaction.amount,
            category=transaction.category
        )
        return transaction
    return None


def get_user_transaction_history(user_id, limit=10):
    """
    Получает историю транзакций пользователя.

    Args:
        user_id (int): ID пользователя
        limit (int, optional): Максимальное количество транзакций

    Returns:
        list: Список объектов Transaction
    """
    # Получаем данные из базы
    transactions_data = db_get_transaction_history(user_id, limit)

    # Преобразуем в объекты Transaction
    transactions = []
    for transaction_data in transactions_data:
        transaction = Transaction.from_db_tuple(transaction_data)
        if transaction:
            transactions.append(transaction)

    return transactions


def filter_user_transactions(user_id, filter_param, limit=20):
    """
    Фильтрует транзакции пользователя по категории или типу.

    Args:
        user_id (int): ID пользователя
        filter_param (str): Параметр фильтрации
        limit (int, optional): Максимальное количество транзакций

    Returns:
        list: Список отфильтрованных объектов Transaction
    """
    # Получаем отфильтрованные данные
    filtered_data = db_filter_transactions(user_id, filter_param, limit)

    # Преобразуем в объекты Transaction
    transactions = []
    for transaction_data in filtered_data:
        transaction = Transaction.from_db_tuple(transaction_data)
        if transaction:
            transactions.append(transaction)

    return transactions


def get_user_last_transaction(user_id):
    """
    Получает последнюю транзакцию пользователя.

    Args:
        user_id (int): ID пользователя

    Returns:
        Transaction: Объект последней транзакции или None
    """
    # Получаем данные последней транзакции
    last_transaction_data = db_get_last_transaction(user_id)

    # Преобразуем в объект Transaction
    if last_transaction_data:
        return Transaction.from_db_tuple(last_transaction_data)
    return None


def delete_user_transaction(transaction_id):
    """
    Удаляет транзакцию пользователя и обновляет бюджет.

    Args:
        transaction_id (int): ID транзакции для удаления

    Returns:
        bool: True если транзакция успешно удалена, иначе False
    """
    # Получаем данные о транзакции перед удалением
    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT user_id, amount, category FROM transactions
            WHERE id = ?
        """, (transaction_id,))
        transaction_data = cursor.fetchone()

        if not transaction_data:
            return False

        user_id, amount, category = transaction_data

        # Удаляем транзакцию
        success = db_delete_transaction(transaction_id)

        if success:
            # Обновляем бюджет с отрицательной суммой (отменяем влияние транзакции)
            db_update_budget(user_id, -amount, category)

        return success
    except Exception as e:
        print(f"Error in delete_user_transaction: {e}")
        return False
    finally:
        conn.close()


def recalculate_user_budget(user_id):
    """
    Пересчитывает весь бюджет пользователя на основе всех его транзакций.

    Args:
        user_id (int): ID пользователя

    Returns:
        bool: True если бюджет успешно пересчитан, иначе False
    """
    return db_recalculate_budget(user_id)
