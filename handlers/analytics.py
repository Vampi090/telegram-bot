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
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    stats_data = get_expense_stats(user_id)

    if not stats_data:
        text = "📊 У вас ще немає даних про витрати."
    else:
        text = "📊 *Статистика витрат за категоріями:*\n"
        for category, total in stats_data:
            text += f"🔹 {category}: {round(total, 2)} грн\n"

    reply_markup = analytics_menu_keyboard()

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def handle_chart_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    file_path = generate_expense_chart(user_id)

    if not file_path:
        await update.callback_query.edit_message_text(
            text="❌ Недостатньо даних для графіка.",
            reply_markup=analytics_menu_keyboard()
        )
        return

    with open(file_path, "rb") as photo:
        await context.bot.send_photo(
            chat_id=user_id,
            photo=photo,
            caption="📊 Ваш графік витрат."
        )

    os.remove(file_path)

    await context.bot.send_message(
        chat_id=user_id,
        text="📊 Графік витрат згенеровано.",
        reply_markup=analytics_menu_keyboard()
    )


async def handle_report_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    report = get_transaction_report(user_id, days=30)

    if report['transaction_count'] == 0:
        text = "📊 У вас ще немає даних про транзакції за останні 30 днів."
    else:
        text = f"📊 *Звіт за останні {report['days']} днів:*\n\n"
        text += f"💰 Доходи: {round(report['total_income'], 2)} грн\n"
        text += f"💸 Витрати: {round(report['total_expense'], 2)} грн\n"
        text += f"📈 Баланс: {round(report['balance'], 2)} грн\n\n"

        if report['top_expense_categories']:
            text += "🔝 *Топ категорії витрат:*\n"
            for category, amount in report['top_expense_categories']:
                text += f"🔹 {category}: {round(abs(amount), 2)} грн\n"

        text += f"\n📝 Всього транзакцій: {report['transaction_count']}"

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=analytics_menu_keyboard()
    )


async def handle_export_command(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.effective_user.id

    file_path = export_transactions_to_excel(user_id)

    if not file_path:
        await update.message.reply_text("❌ У вас немає даних для експорту.")
        return

    with open(file_path, "rb") as doc:
        await context.bot.send_document(
            chat_id=user_id,
            document=doc,
            filename=f"transactions_{user_id}.xlsx",
            caption="📁 Ваші дані експортовані в Excel з форматуванням."
        )

    os.remove(file_path)


analytics_handler = CallbackQueryHandler(handle_analytics_callback, pattern='^analytics$')
stats_handler = CallbackQueryHandler(handle_stats_callback, pattern='^stats$')
chart_handler = CallbackQueryHandler(handle_chart_callback, pattern='^chart$')
report_handler = CallbackQueryHandler(handle_report_callback, pattern='^report$')
export_handler = CommandHandler('export', handle_export_command)
