from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def budget_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🐷 Скарбничка", callback_data='piggy_bank')],
        [InlineKeyboardButton("💰 Бюджет", callback_data='budget')],
        [InlineKeyboardButton("⏰ Нагадування", callback_data='reminder')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ])
