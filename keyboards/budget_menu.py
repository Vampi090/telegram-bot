from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Подменю: Цели и бюджет
def budget_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Цілі", callback_data='goal')],
        [InlineKeyboardButton("💰 Бюджет", callback_data='budget')],
        [InlineKeyboardButton("⏰ Нагадування", callback_data='reminder')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ])