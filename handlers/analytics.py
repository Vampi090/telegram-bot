from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from keyboards.analytics_menu import analytics_menu_keyboard
from services.logging_service import log_command_usage
from services.analytics_service import (
    get_expense_stats,
    generate_expense_chart,
    export_transactions_to_excel,
    get_transaction_report
)
import os


async def handle_analytics_callback(update: Update, context: CallbackContext):
    """Обработчик для меню аналитики"""
    await log_command_usage(update, context)
    user = update.effective_user

    reply_markup = analytics_menu_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="📥 Меню аналітики",
            reply_markup=reply_markup
        )


async def handle_stats_callback(update: Update, context: CallbackContext):
    """Обработчик для просмотра статистики расходов"""
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    # Получаем статистику расходов
    stats_data = get_expense_stats(user_id)

    if not stats_data:
        text = "📊 У вас еще нет данных о расходах."
    else:
        text = "📊 *Статистика расходов по категориям:*\n"
        for category, total in stats_data:
            text += f"🔹 {category}: {round(total, 2)} грн\n"

    # Создаем клавиатуру с кнопкой "Назад"
    reply_markup = analytics_menu_keyboard()

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def handle_chart_callback(update: Update, context: CallbackContext):
    """Обработчик для просмотра графиков расходов"""
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    # Генерируем график расходов
    file_path = generate_expense_chart(user_id)

    if not file_path:
        await update.callback_query.edit_message_text(
            text="❌ Недостаточно данных для графика.",
            reply_markup=analytics_menu_keyboard()
        )
        return

    # Отправляем график
    with open(file_path, "rb") as photo:
        await context.bot.send_photo(
            chat_id=user_id, 
            photo=photo, 
            caption="📊 Ваш график расходов."
        )

    # Удаляем временный файл
    os.remove(file_path)

    # Отправляем сообщение с меню аналитики
    await context.bot.send_message(
        chat_id=user_id,
        text="📊 График расходов сгенерирован.",
        reply_markup=analytics_menu_keyboard()
    )


async def handle_report_callback(update: Update, context: CallbackContext):
    """Обработчик для просмотра отчета о транзакциях"""
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    # Получаем отчет о транзакциях за 30 дней
    report = get_transaction_report(user_id, days=30)

    if report['transaction_count'] == 0:
        text = "📊 У вас еще нет данных о транзакциях за последние 30 дней."
    else:
        text = f"📊 *Отчет за последние {report['days']} дней:*\n\n"
        text += f"💰 Доходы: {round(report['total_income'], 2)} грн\n"
        text += f"💸 Расходы: {round(report['total_expense'], 2)} грн\n"
        text += f"📈 Баланс: {round(report['balance'], 2)} грн\n\n"

        if report['top_expense_categories']:
            text += "🔝 *Топ категории расходов:*\n"
            for category, amount in report['top_expense_categories']:
                text += f"🔹 {category}: {round(abs(amount), 2)} грн\n"

        text += f"\n📝 Всего транзакций: {report['transaction_count']}"

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=analytics_menu_keyboard()
    )


async def handle_export_command(update: Update, context: CallbackContext):
    """Обработчик для экспорта транзакций в Excel"""
    await log_command_usage(update, context)

    user_id = update.effective_user.id

    # Экспортируем транзакции в Excel
    file_path = export_transactions_to_excel(user_id)

    if not file_path:
        await update.message.reply_text("❌ У вас нет данных для экспорта.")
        return

    # Отправляем Excel файл
    with open(file_path, "rb") as doc:
        await context.bot.send_document(
            chat_id=user_id,
            document=doc,
            filename=f"transactions_{user_id}.xlsx",
            caption="📁 Ваши данные экспортированы в Excel с форматированием."
        )

    # Удаляем временный файл
    os.remove(file_path)


# Регистрация обработчиков
analytics_handler = CallbackQueryHandler(handle_analytics_callback, pattern='^analytics$')
stats_handler = CallbackQueryHandler(handle_stats_callback, pattern='^stats$')
chart_handler = CallbackQueryHandler(handle_chart_callback, pattern='^chart$')
report_handler = CallbackQueryHandler(handle_report_callback, pattern='^report$')
export_handler = CommandHandler('export', handle_export_command)
