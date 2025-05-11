from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def transaction_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Додати транзакцію", callback_data='add')],
        [InlineKeyboardButton("📜 Історія", callback_data='history')],
        [InlineKeyboardButton("↩️ Відміна транзакції", callback_data='undo')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ])