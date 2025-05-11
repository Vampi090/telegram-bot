from datetime import datetime


class Transaction:
    def __init__(self, id=None, user_id=None, amount=0.0, category="", transaction_type=None, timestamp=None):
        self.id = id
        self.user_id = user_id
        self.amount = amount
        self.category = category

        if transaction_type is None:
            self.transaction_type = "дохід" if amount > 0 else "витрата"
        else:
            self.transaction_type = transaction_type

        if timestamp is None:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.timestamp = timestamp

    @classmethod
    def from_db_tuple(cls, db_tuple):
        if not db_tuple:
            return None

        if len(db_tuple) == 5:
            id, amount, category, transaction_type, timestamp = db_tuple
            return cls(id=id, amount=amount, category=category,
                       transaction_type=transaction_type, timestamp=timestamp)
        elif len(db_tuple) == 4:
            timestamp, amount, category, transaction_type = db_tuple
            return cls(amount=amount, category=category,
                       transaction_type=transaction_type, timestamp=timestamp)
        else:
            return None

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'category': self.category,
            'type': self.transaction_type,
            'timestamp': self.timestamp
        }

    def __str__(self):
        return f"📅 {self.timestamp} | 💰 {self.amount} | 📂 {self.category} ({self.transaction_type})"
