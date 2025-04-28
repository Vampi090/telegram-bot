from models.transaction import Transaction
from services.database_service import (
    add_transaction as db_add_transaction,
    get_transaction_history as db_get_transaction_history,
    filter_transactions_by_category_or_type as db_filter_transactions,
    get_last_transaction as db_get_last_transaction,
    delete_transaction as db_delete_transaction
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
    Удаляет транзакцию пользователя.
    
    Args:
        transaction_id (int): ID транзакции для удаления
        
    Returns:
        bool: True если транзакция успешно удалена, иначе False
    """
    return db_delete_transaction(transaction_id)