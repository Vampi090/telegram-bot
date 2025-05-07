from datetime import datetime

class Debt:
    """
    Модель для представления долга.
    """
    def __init__(self, id=None, user_id=None, debtor="", amount=0.0, status="open", due_date=None):
        """
        Инициализирует новый объект долга.

        Args:
            id (int, optional): ID долга в базе данных
            user_id (int, optional): ID пользователя
            debtor (str, optional): Имя должника или кредитора
            amount (float, optional): Сумма долга
            status (str, optional): Статус долга (open/closed)
            due_date (str, optional): Дата создания или срок погашения долга
        """
        self.id = id
        self.user_id = user_id
        self.debtor = debtor
        self.amount = amount
        self.status = status

        # Устанавливаем текущее время, если не указано
        if due_date is None:
            self.due_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.due_date = due_date

    @classmethod
    def from_db_tuple(cls, db_tuple):
        """
        Создает объект Debt из кортежа базы данных.

        Args:
            db_tuple (tuple): Кортеж из базы данных (id, user_id, debtor, amount, status, due_date)

        Returns:
            Debt: Новый объект Debt
        """
        if not db_tuple:
            return None

        if len(db_tuple) == 6:  # Если в кортеже 6 элементов (id, user_id, debtor, amount, status, due_date)
            id, user_id, debtor, amount, status, due_date = db_tuple
            return cls(id=id, user_id=user_id, debtor=debtor, amount=amount, 
                      status=status, due_date=due_date)
        elif len(db_tuple) == 4:  # Если в кортеже 4 элемента (debtor, amount, status, due_date)
            debtor, amount, status, due_date = db_tuple
            return cls(debtor=debtor, amount=amount, status=status, due_date=due_date)
        elif len(db_tuple) == 2:  # Если в кортеже 2 элемента (debtor, amount)
            debtor, amount = db_tuple
            return cls(debtor=debtor, amount=amount)
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
            'debtor': self.debtor,
            'amount': self.amount,
            'status': self.status,
            'due_date': self.due_date
        }

    def __str__(self):
        """
        Возвращает строковое представление долга.

        Returns:
            str: Строковое представление долга
        """
        return f"👤 {self.debtor} | 💰 {self.amount}₴ | ✅ {self.status} | 📅 {self.due_date}"
