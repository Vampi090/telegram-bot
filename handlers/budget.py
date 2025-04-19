from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from keyboards.budget_menu import budget_menu_keyboard
from services.logging_service import log_command_usage


async def handle_budgeting_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)
    user = update.effective_user

    reply_markup = budget_menu_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="📥 Меню бюджету",
            reply_markup=reply_markup
        )


budgeting_handler = CallbackQueryHandler(handle_budgeting_callback, pattern='^budgeting$')