from datetime import datetime


class Debt:
    def __init__(self, id=None, user_id=None, debtor="", amount=0.0, status="open", due_date=None):
        self.id = id
        self.user_id = user_id
        self.debtor = debtor
        self.amount = amount
        self.status = status

        if due_date is None:
            self.due_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.due_date = due_date

    @classmethod
    def from_db_tuple(cls, db_tuple):
        if not db_tuple:
            return None

        if len(db_tuple) == 6:
            id, user_id, debtor, amount, status, due_date = db_tuple
            return cls(id=id, user_id=user_id, debtor=debtor, amount=amount,
                       status=status, due_date=due_date)
        elif len(db_tuple) == 4:
            debtor, amount, status, due_date = db_tuple
            return cls(debtor=debtor, amount=amount, status=status, due_date=due_date)
        elif len(db_tuple) == 2:
            debtor, amount = db_tuple
            return cls(debtor=debtor, amount=amount)
        else:
            return None

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'debtor': self.debtor,
            'amount': self.amount,
            'status': self.status,
            'due_date': self.due_date
        }

    def __str__(self):
        return f"👤 {self.debtor} | 💰 {self.amount}₴ | ✅ {self.status} | 📅 {self.due_date}"
