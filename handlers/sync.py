from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from keyboards.sync_menu import sync_menu_keyboard
from services.logging_service import log_command_usage
from services.sync_service import sync_with_google_sheets
from services.analytics_service import export_transactions_to_excel
import os


async def handle_sync_menu_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)
    user = update.effective_user

    reply_markup = sync_menu_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="📥 Меню синхронізації та експорту",
            reply_markup=reply_markup
        )


async def handle_sync_callback(update: Update, context: CallbackContext):
    """Обробник для синхронізації з Google Sheets"""
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    await update.callback_query.edit_message_text(
        text="🔄 Синхронізація даних запущена...",
        reply_markup=None
    )

    success, message = sync_with_google_sheets(user_id)

    await context.bot.send_message(
        chat_id=user_id,
        text=message,
        reply_markup=sync_menu_keyboard()
    )


async def handle_export_callback(update: Update, context: CallbackContext):
    """Обробник для експорту даних в Excel"""
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    file_path = export_transactions_to_excel(user_id)

    if not file_path:
        await update.callback_query.edit_message_text(
            text="❌ У вас немає даних для експорту.",
            reply_markup=sync_menu_keyboard()
        )
        return

    with open(file_path, "rb") as doc:
        await context.bot.send_document(
            chat_id=user_id,
            document=doc,
            filename=f"transactions_{user_id}.xlsx",
            caption="📁 Ваші дані експортовані в Excel з форматуванням."
        )

    os.remove(file_path)

    await context.bot.send_message(
        chat_id=user_id,
        text="📁 Експорт даних в Excel завершено.",
        reply_markup=sync_menu_keyboard()
    )


sync_menu_handler = CallbackQueryHandler(handle_sync_menu_callback, pattern='^sync_export')
sync_handler = CallbackQueryHandler(handle_sync_callback, pattern='^sync$')
export_callback_handler = CallbackQueryHandler(handle_export_callback, pattern='^export$')
