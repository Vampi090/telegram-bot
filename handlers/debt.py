from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from keyboards.debt_menu import debt_menu_keyboard
from services.logging_service import log_command_usage


async def handle_debt_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)
    user = update.effective_user

    reply_markup = debt_menu_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="🤝 Облік боргів",
            reply_markup=reply_markup
        )


debt_handler = CallbackQueryHandler(handle_debt_callback, pattern='^debt')