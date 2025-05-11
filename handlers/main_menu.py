from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from handlers.start import start
from services.logging_service import log_command_usage


async def handle_back_to_main_menu(update: Update, context: CallbackContext):
    await log_command_usage(update, context)
    await start(update, context)


back_to_main_menu_handler = CallbackQueryHandler(handle_back_to_main_menu, pattern='^main_menu$')
