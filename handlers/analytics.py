from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from keyboards.analytics_menu import analytics_menu_keyboard
from services.logging_service import log_command_usage


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


analytics_handler = CallbackQueryHandler(handle_analytics_callback, pattern='^analytics$')