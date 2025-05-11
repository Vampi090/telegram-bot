from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def analytics_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Статистика", callback_data='stats')],
        [InlineKeyboardButton("📊 Графіки", callback_data='chart')],
        [InlineKeyboardButton("📅 Звіт", callback_data='report')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ])