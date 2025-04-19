from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from keyboards.transaction_menu import transaction_menu_keyboard
from services.logging_service import log_command_usage


async def handle_transactions_callback(update: Update, context: CallbackContext):
    """
    Обработчик кнопки 📥 Транзакції (callback_data='transactions').
    """
    await log_command_usage(update, context)
    user = update.effective_user

    reply_markup = transaction_menu_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="📥 Меню керування транзакціями",
            reply_markup=reply_markup
        )


transactions_handler = CallbackQueryHandler(handle_transactions_callback, pattern='^transactions$')