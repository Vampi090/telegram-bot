from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from keyboards.tools_menu import tools_menu_keyboard
from services.logging_service import log_command_usage


async def handle_tools_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)
    user = update.effective_user

    reply_markup = tools_menu_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="📥 Меню фінансових інструментів",
            reply_markup=reply_markup
        )


tools_handler = CallbackQueryHandler(handle_tools_callback, pattern='^tools')