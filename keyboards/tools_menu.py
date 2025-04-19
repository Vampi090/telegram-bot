from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Подменю: Финансовые инструменты
def tools_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💱 Конвертація валют", callback_data='convert')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ])