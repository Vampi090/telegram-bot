from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def debt_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Мои долги", callback_data="view_debts")],
        [InlineKeyboardButton("➕ Добавить долг", callback_data="add_debt")],
        [InlineKeyboardButton("📚 История долгов", callback_data="debt_history")],
        [InlineKeyboardButton("✅ Закрыть долг", callback_data="close_debt")],
        [InlineKeyboardButton("🔔 Напоминание", callback_data="remind_debt")],
        [InlineKeyboardButton("🆘 Помощь", callback_data="help_debt")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ])