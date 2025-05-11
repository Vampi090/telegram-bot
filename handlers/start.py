from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from keyboards.main_menu import main_menu_keyboard
from services.logging_service import log_command_usage
from utils.menu_utils import send_or_edit_menu


async def start(update: Update, context: CallbackContext):
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

    await send_or_edit_menu(update, context, welcome_text, reply_markup)


start_handler = CommandHandler("start", start)
