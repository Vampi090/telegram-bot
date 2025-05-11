from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def reminder_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Створити нагадування", callback_data='create_reminder')],
        [InlineKeyboardButton("📋 Мої нагадування", callback_data='list_reminders')],
        [InlineKeyboardButton("🔙 Назад", callback_data='budgeting')]
    ])
