from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext, 
    CallbackQueryHandler, 
    CommandHandler, 
    ConversationHandler,
    MessageHandler,
    filters
)
from keyboards.debt_menu import debt_menu_keyboard
from services.logging_service import log_command_usage
from services.database_service import save_debt, get_active_debts, get_debt_history, close_debt
from datetime import datetime, time

# Состояния для ConversationHandler
DEBT_NAME, DEBT_AMOUNT = range(2)


async def handle_debt_callback(update: Update, context: CallbackContext):
    """Обработчик для кнопки 'Долги' в главном меню"""
    await log_command_usage(update, context)
    user = update.effective_user

    reply_markup = debt_menu_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="🤝 Облік боргів",
            reply_markup=reply_markup
        )
    elif update.message:
        await update.message.reply_text(
            text="🤝 Облік боргів",
            reply_markup=reply_markup
        )


async def debt_menu_button_handler(update: Update, context: CallbackContext):
    """Обработчик кнопок меню долгов"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "view_debts":
        debts = get_active_debts(user_id)
        text = (
            "📜 Ваши долги:\n" + "\n".join(f"{d[0]}: {d[1]}₽" for d in debts)
            if debts else "✅ У вас нет долгов."
        )
        await query.message.edit_text(text, reply_markup=generate_back_button())

    elif query.data == "debt_history":
        history = get_debt_history(user_id)
        text = (
            "📚 История долгов:\n" + "\n".join(f"{row[0]}: {row[1]}₽ ({row[2]}) — {row[3]}" for row in history)
            if history else "История пуста."
        )
        await query.message.edit_text(text, reply_markup=generate_back_button())

    elif query.data == "close_debt":
        await query.message.edit_text(
            "✅ Укажите, какой долг вы хотите закрыть (введите имя и сумму через пробел):",
            reply_markup=generate_back_button()
        )
        # Устанавливаем состояние для обработки следующего сообщения
        context.user_data["waiting_for_close_debt"] = True

    elif query.data == "add_debt":
        text = (
            "➕ *Как добавить долг:*\n\n"
            "Вы можете добавить долг вручную с помощью команды:\n"
            "`/adddebt Имя Сумма`\n\n"
            "*Пример:* `/adddebt Алексей 3000`\n"
            "Это создаст запись о долге в вашу базу данных."
        )
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=generate_back_button())

    elif query.data == "remind_debt":
        await set_daily_reminder(update, context)
        await query.message.edit_text(
            "🔔 Напоминание установлено. Вы будете получать уведомления каждый день в 9:00.",
            reply_markup=generate_back_button()
        )

    elif query.data == "help_debt":
        help_text = (
            "🆘 *Помощь по долгам:*\n\n"
            "➕ Добавить долг — добавляет нового должника/долг.\n"
            "📜 Мои долги — список активных долгов.\n"
            "📚 История — все долги, включая закрытые.\n"
            "✅ Закрыть долг — отметить как погашенный.\n"
            "🔔 Напоминание — ежедневное напоминание в 9:00.\n"
            "🔙 Главное меню — возврат в основное меню."
        )
        await query.message.edit_text(help_text, parse_mode="Markdown", reply_markup=generate_back_button())

    elif query.data == "debt_back":
        await handle_debt_callback(update, context)


async def handle_message(update: Update, context: CallbackContext):
    """Обработчик сообщений для закрытия долга"""
    if context.user_data.get("waiting_for_close_debt"):
        try:
            parts = update.message.text.split()
            if len(parts) < 2:
                await update.message.reply_text("❌ Пожалуйста, укажите имя и сумму через пробел.")
                return

            name = parts[0]
            amount = float(parts[1])

            if close_debt(update.effective_user.id, name, amount):
                await update.message.reply_text(f"✅ Долг {name} на сумму {amount}₽ закрыт.")
            else:
                await update.message.reply_text(f"❌ Долг {name} на сумму {amount}₽ не найден.")

            # Сбрасываем состояние
            context.user_data["waiting_for_close_debt"] = False

        except ValueError:
            await update.message.reply_text("❌ Пожалуйста, укажите корректную сумму.")


async def ask_debt_name(update: Update, context: CallbackContext):
    """Запрашивает имя должника"""
    await update.message.reply_text("Введите имя человека, которому вы должны или который должен вам:")
    return DEBT_NAME


async def ask_debt_amount(update: Update, context: CallbackContext):
    """Запрашивает сумму долга"""
    context.user_data["debt_name"] = update.message.text
    await update.message.reply_text("Введите сумму долга:")
    return DEBT_AMOUNT


async def save_debt_handler(update: Update, context: CallbackContext):
    """Сохраняет долг в базу данных"""
    user_id = update.effective_user.id
    debt_name = context.user_data.get("debt_name")
    try:
        amount = float(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Введите корректное число.")
        return DEBT_AMOUNT

    if save_debt(user_id, debt_name, amount):
        await update.message.reply_text(f"✅ Долг сохранён: {debt_name} — {amount}₽")
    else:
        await update.message.reply_text("❌ Произошла ошибка при сохранении долга.")

    return ConversationHandler.END


async def cancel_add_debt(update: Update, context: CallbackContext):
    """Отменяет добавление долга"""
    await update.message.reply_text("🚫 Добавление долга отменено.")
    return ConversationHandler.END


async def send_debt_reminder(context: CallbackContext):
    """Отправляет напоминание о долгах"""
    job = context.job
    user_id = job.chat_id
    debts = get_active_debts(user_id)
    if debts:
        text = "🔔 Напоминание о долгах:\n" + "\n".join(f"{d[0]}: {d[1]}₽" for d in debts)
        await context.bot.send_message(chat_id=user_id, text=text)


async def set_daily_reminder(update: Update, context: CallbackContext):
    """Устанавливает ежедневное напоминание о долгах"""
    chat_id = update.effective_chat.id

    # Удаляем существующие напоминания для этого чата
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    # Устанавливаем новое напоминание
    context.job_queue.run_daily(
        send_debt_reminder,
        time=time(hour=9, minute=0),
        chat_id=chat_id,
        name=str(chat_id)
    )

    if update.callback_query:
        await update.callback_query.answer("Напоминания установлены")
    else:
        await update.message.reply_text("✅ Напоминания будут приходить каждый день в 9:00.")


async def adddebt_command(update: Update, context: CallbackContext):
    """Обработчик команды /adddebt"""
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("❌ Формат: `/adddebt имя сумма`\nПример: `/adddebt Алексей 3000`", parse_mode="Markdown")
            return

        name = args[0]
        amount = float(args[1])

        if save_debt(update.effective_user.id, name, amount):
            await update.message.reply_text(f"✅ Долг добавлен: {name} — {amount}₽")
        else:
            await update.message.reply_text("❌ Произошла ошибка при сохранении долга.")

    except (ValueError, IndexError):
        await update.message.reply_text("❌ Формат: `/adddebt имя сумма`\nПример: `/adddebt Алексей 3000`", parse_mode="Markdown")


def generate_back_button():
    """Генерирует кнопку 'Назад'"""
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="debt_back")]]
    return InlineKeyboardMarkup(keyboard)


# Регистрация обработчиков
debt_handler = CallbackQueryHandler(handle_debt_callback, pattern='^debt$')
debt_command_handler = CommandHandler("debt", handle_debt_callback)
debt_menu_handler = CallbackQueryHandler(debt_menu_button_handler, pattern='^(view_debts|debt_history|close_debt|add_debt|remind_debt|help_debt|debt_back)$')
debt_message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
adddebt_handler = CommandHandler("adddebt", adddebt_command)
set_reminder_handler = CommandHandler("debtreminder", set_daily_reminder)

# Обработчик диалога добавления долга
add_debt_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("adddebt_dialog", ask_debt_name)],
    states={
        DEBT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_debt_amount)],
        DEBT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_debt_handler)]
    },
    fallbacks=[CommandHandler("cancel", cancel_add_debt)]
)
