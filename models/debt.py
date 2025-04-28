from datetime import datetime

class Debt:
    """
    Модель для представления долга.
    """
    def __init__(self, id=None, user_id=None, name="", amount=0.0, status="open", timestamp=None):
        """
        Инициализирует новый объект долга.
        
        Args:
            id (int, optional): ID долга в базе данных
            user_id (int, optional): ID пользователя
            name (str, optional): Имя должника или кредитора
            amount (float, optional): Сумма долга
            status (str, optional): Статус долга (open/closed)
            timestamp (str, optional): Временная метка создания долга
        """
        self.id = id
        self.user_id = user_id
        self.name = name
        self.amount = amount
        self.status = status
            
        # Устанавливаем текущее время, если не указано
        if timestamp is None:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.timestamp = timestamp
    
    @classmethod
    def from_db_tuple(cls, db_tuple):
        """
        Создает объект Debt из кортежа базы данных.
        
        Args:
            db_tuple (tuple): Кортеж из базы данных (id, user_id, name, amount, status, timestamp)
            
        Returns:
            Debt: Новый объект Debt
        """
        if not db_tuple:
            return None
            
        if len(db_tuple) == 6:  # Если в кортеже 6 элементов (id, user_id, name, amount, status, timestamp)
            id, user_id, name, amount, status, timestamp = db_tuple
            return cls(id=id, user_id=user_id, name=name, amount=amount, 
                      status=status, timestamp=timestamp)
        elif len(db_tuple) == 4:  # Если в кортеже 4 элемента (name, amount, status, timestamp)
            name, amount, status, timestamp = db_tuple
            return cls(name=name, amount=amount, status=status, timestamp=timestamp)
        elif len(db_tuple) == 2:  # Если в кортеже 2 элемента (name, amount)
            name, amount = db_tuple
            return cls(name=name, amount=amount)
        else:
            return None
    
    def to_dict(self):
        """
        Преобразует объект Debt в словарь.
        
        Returns:
            dict: Словарь с данными долга
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'amount': self.amount,
            'status': self.status,
            'timestamp': self.timestamp
        }
    
    def __str__(self):
        """
        Возвращает строковое представление долга.
        
        Returns:
            str: Строковое представление долга
        """
        return f"👤 {self.name} | 💰 {self.amount}₽ | ✅ {self.status} | 📅 {self.timestamp}"