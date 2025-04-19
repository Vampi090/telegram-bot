from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from handlers.start import start
from services.logging_service import log_command_usage


# Обработчик кнопки "🔙 Назад"
async def handle_back_to_main_menu(update: Update, context: CallbackContext):
    """
    Обработчик кнопки, возвращающей пользователя на главное меню (вызывает start).
    """
    await log_command_usage(update, context)  # Логирование события

    # Переадресация на обработчик start
    await start(update, context)


# CallbackQueryHandler для кнопки "Назад"
back_to_main_menu_handler = CallbackQueryHandler(handle_back_to_main_menu, pattern='^main_menu$')
