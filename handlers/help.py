from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from keyboards.help_menu import help_menu_keyboard
from services.logging_service import log_command_usage


async def handle_help_callback(update: Update, context: CallbackContext):
    """Обработчик для меню помощи"""
    await log_command_usage(update, context)
    user = update.effective_user

    reply_markup = help_menu_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="❓ Допомога",
            reply_markup=reply_markup
        )


async def help_command(update: Update, context: CallbackContext):
    """Функция помощи (список команд)"""
    await log_command_usage(update, context)

    help_text = """
📌 *Доступные команды:*
/start — Запуск бота  
/add [сумма] [категория] — Добавить транзакцию  
/history — История транзакций  
/stats — Статистика расходов  
/goal — Управление целями  
/undo — Отмена последней транзакции  
/export — Экспорт данных  
/chart — Графики расходов  
/reminder — Напоминания о бюджете  
/budget — Управление бюджетом  
/convert — Конвертация валют  
/sync — Синхронизация с Google Таблицами  
/report [месяц] — Сводка за месяц  
/debt — Учет долгов
"""

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=help_text,
            parse_mode="Markdown",
            reply_markup=help_menu_keyboard()
        )
    elif update.message:
        await update.message.reply_text(
            help_text,
            parse_mode="Markdown",
            reply_markup=help_menu_keyboard()
        )


async def handle_guide_callback(update: Update, context: CallbackContext):
    """Обработчик для мини-гайда"""
    await log_command_usage(update, context)

    guide_text = """
📖 *Мини-гайд по использованию бота:*

1️⃣ *Добавление транзакций*
   • Используйте команду /add или кнопку "Добавить" в меню
   • Укажите сумму (положительную для доходов, отрицательную для расходов)
   • Добавьте название или категорию

2️⃣ *Просмотр истории*
   • Команда /history или кнопка "История" покажет последние транзакции

3️⃣ *Аналитика*
   • В разделе "Аналитика" доступны статистика, графики и отчеты
   • Используйте /stats для быстрого просмотра статистики

4️⃣ *Управление бюджетом*
   • Создавайте финансовые цели через /goal
   • Устанавливайте бюджеты с помощью /budget

5️⃣ *Дополнительные функции*
   • Конвертация валют: /convert
   • Учет долгов: /debt
   • Экспорт данных: /export
"""

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=guide_text,
            parse_mode="Markdown",
            reply_markup=help_menu_keyboard()
        )


# Регистрация обработчиков
help_section_handler = CallbackQueryHandler(handle_help_callback, pattern='^help_section$')
help_handler = CommandHandler("help", help_command)
guide_handler = CallbackQueryHandler(handle_guide_callback, pattern='^guide$')
help_callback_handler = CallbackQueryHandler(help_command, pattern='^help$')
