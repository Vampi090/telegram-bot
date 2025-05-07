from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Подменю: Помощь
def help_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Гайд", callback_data='guide')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ])
