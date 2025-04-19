from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from keyboards.main_menu import main_menu_keyboard
from services.logging_service import log_command_usage


async def start(update: Update, context: CallbackContext):
    """
    Обработчик команды /start – отправляет приветственное сообщение и подгружает главное меню.
    """
    await log_command_usage(update, context)
    user = update.effective_user

    welcome_text = (
        f"👋 Привіт, {user.first_name}!\n\n"
        "Я допоможу тобі керувати фінансами: відстежувати доходи та витрати, вести бюджет, ставити цілі та багато іншого.\n\n"
        "Ось що я вмію:\n"
        "• ➕ Додавати транзакції (/add)\n"
        "• 📜 Показувати історію (/history)\n"
        "• 📊 Аналізувати статистику (/stats)\n"
        "• 💰 Вести облік боргів (/debt)\n"
        "• 🎯 Допомагати досягати фінансових цілей (/goal)\n\n"
        "👇 Обери дію:"
    )

    reply_markup = main_menu_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)


# Создаем обработчик для команды /start
start_handler = CommandHandler("start", start)