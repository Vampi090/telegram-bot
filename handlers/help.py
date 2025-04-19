from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from keyboards.help_menu import help_menu_keyboard
from services.logging_service import log_command_usage


async def handle_help_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)
    user = update.effective_user

    reply_markup = help_menu_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="❓ Допомога",
            reply_markup=reply_markup
        )


help_handler = CallbackQueryHandler(handle_help_callback, pattern='^help_section')