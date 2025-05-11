from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def help_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Гайд", callback_data='guide')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ])
