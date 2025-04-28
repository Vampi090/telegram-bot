from datetime import datetime

class Transaction:
    """
    Модель для представления транзакции.
    """
    def __init__(self, id=None, user_id=None, amount=0.0, category="", transaction_type=None, timestamp=None):
        """
        Инициализирует новый объект транзакции.
        
        Args:
            id (int, optional): ID транзакции в базе данных
            user_id (int, optional): ID пользователя
            amount (float, optional): Сумма транзакции
            category (str, optional): Категория транзакции
            transaction_type (str, optional): Тип транзакции (доход/расход)
            timestamp (str, optional): Временная метка транзакции
        """
        self.id = id
        self.user_id = user_id
        self.amount = amount
        self.category = category
        
        # Определяем тип транзакции автоматически, если не указан
        if transaction_type is None:
            self.transaction_type = "доход" if amount > 0 else "расход"
        else:
            self.transaction_type = transaction_type
            
        # Устанавливаем текущее время, если не указано
        if timestamp is None:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.timestamp = timestamp
    
    @classmethod
    def from_db_tuple(cls, db_tuple):
        """
        Создает объект Transaction из кортежа базы данных.
        
        Args:
            db_tuple (tuple): Кортеж из базы данных (id, user_id, amount, category, type, timestamp)
            
        Returns:
            Transaction: Новый объект Transaction
        """
        if not db_tuple:
            return None
            
        if len(db_tuple) == 5:  # Если в кортеже 5 элементов (id, amount, category, type, timestamp)
            id, amount, category, transaction_type, timestamp = db_tuple
            return cls(id=id, amount=amount, category=category, 
                      transaction_type=transaction_type, timestamp=timestamp)
        elif len(db_tuple) == 4:  # Если в кортеже 4 элемента (timestamp, amount, category, type)
            timestamp, amount, category, transaction_type = db_tuple
            return cls(amount=amount, category=category, 
                      transaction_type=transaction_type, timestamp=timestamp)
        else:
            return None
    
    def to_dict(self):
        """
        Преобразует объект Transaction в словарь.
        
        Returns:
            dict: Словарь с данными транзакции
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'category': self.category,
            'type': self.transaction_type,
            'timestamp': self.timestamp
        }
    
    def __str__(self):
        """
        Возвращает строковое представление транзакции.
        
        Returns:
            str: Строковое представление транзакции
        """
        return f"📅 {self.timestamp} | 💰 {self.amount} | 📂 {self.category} ({self.transaction_type})"