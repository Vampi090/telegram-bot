from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def tools_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💱 Конвертація валют", callback_data='convert')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ])