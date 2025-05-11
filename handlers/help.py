from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from keyboards.help_menu import help_menu_keyboard
from services.logging_service import log_command_usage


async def handle_help_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)
    user = update.effective_user

    reply_markup = help_menu_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="❓ Допомога та інструкції",
            reply_markup=reply_markup
        )


async def handle_guide_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    guide_text = """
📖 <b>Повний посібник з використання бота:</b>

1️⃣ <b>Управління транзакціями</b>
   • /add [сума] [категорія] - Додати транзакцію (позитивна сума для доходів, негативна для витрат)
   • /history - Переглянути історію транзакцій
   • /undo - Скасувати останню транзакцію
   • /transactions - Фільтрувати транзакції за категоріями або датами

2️⃣ <b>Аналітика та звіти</b>
   • /stats - Переглянути статистику витрат за категоріями
   • /chart - Згенерувати графіки витрат
   • /report [місяць] - Отримати звіт за місяць
   • /export - Експортувати дані в Excel

3️⃣ <b>Бюджет та фінансові цілі</b>
   • /budget - Встановити та керувати місячним бюджетом
   • /goal - Створити та відстежувати фінансові цілі
   • /track_goals - Перевірити прогрес досягнення цілей
   • /reminder - Встановити нагадування про бюджет

4️⃣ <b>Облік боргів</b>
   • /debt - Переглянути та керувати боргами
   • /adddebt - Швидко додати новий борг
   • /debtreminder - Встановити нагадування про борги

5️⃣ <b>Фінансові інструменти</b>
   • /convert - Конвертувати валюти
   • /advice - Отримати фінансові поради

6️⃣ <b>Синхронізація та експорт</b>
   • /sync - Синхронізувати дані з Google Таблицями
   • /export - Експортувати транзакції в Excel

7️⃣ <b>Загальні команди</b>
   • /start - Запустити бота та відкрити головне меню
"""

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=guide_text,
            parse_mode="HTML",
            reply_markup=help_menu_keyboard()
        )


help_section_handler = CallbackQueryHandler(handle_help_callback, pattern='^help_section$')
guide_handler = CallbackQueryHandler(handle_guide_callback, pattern='^guide$')
