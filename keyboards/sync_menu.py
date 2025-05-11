from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def sync_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Синхронізація з Google Таблицями", callback_data='sync')],
        [InlineKeyboardButton("📊 Експорт даних в Excel", callback_data='export')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ])
