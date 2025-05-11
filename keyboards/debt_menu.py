from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def debt_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Мої борги", callback_data="view_debts")],
        [InlineKeyboardButton("➕ Додати борг", callback_data="add_debt")],
        [InlineKeyboardButton("📚 Історія боргів", callback_data="debt_history")],
        [InlineKeyboardButton("✅ Закрити борг", callback_data="close_debt")],
        # [InlineKeyboardButton("🔔 Нагадування", callback_data="remind_debt")],
        [InlineKeyboardButton("🆘 Допомога", callback_data="help_debt")],
        [InlineKeyboardButton("🔙 Головне меню", callback_data="main_menu")]
    ])
