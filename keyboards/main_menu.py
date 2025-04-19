from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Транзакції", callback_data='transactions')],
        [InlineKeyboardButton("📊 Аналітика та звіти", callback_data='analytics')],
        [InlineKeyboardButton("🎯 Цілі та бюджет", callback_data='budgeting')],
        [InlineKeyboardButton("💼 Фінансові інструменти", callback_data='tools')],
        [InlineKeyboardButton("🔄 Синхронізація та експорт", callback_data='sync_export')],
        [InlineKeyboardButton("🤝 Облік боргів", callback_data='debt')],
        [InlineKeyboardButton("❓ Допомога", callback_data='help_section')],
    ])