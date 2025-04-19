from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from keyboards.sync_menu import sync_menu_keyboard
from services.logging_service import log_command_usage


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


sync_menu_handler = CallbackQueryHandler(handle_sync_menu_callback, pattern='^sync_export')