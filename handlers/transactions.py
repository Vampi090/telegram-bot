from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler, MessageHandler, filters
from keyboards.transaction_menu import transaction_menu_keyboard
from services.logging_service import log_command_usage
from services.transaction_service import (
    add_new_transaction,
    get_user_transaction_history,
    filter_user_transactions,
    get_user_last_transaction,
    delete_user_transaction
)
from models.transaction import Transaction


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


async def add_transaction(update: Update, context: CallbackContext):
    """Обработка команды /add"""
    await log_command_usage(update, context)
    message = update.message  # Сообщение пользователя

    if not message or not context.args:  # Проверяем, есть ли сообщение и аргументы
        if message:  # Только если пользователь сам ввел неверный формат
            await message.reply_text(
                "⚠️ Неверный формат! Используйте: `/add сумма категория`\nПример: `/add 500 еда`",
                parse_mode="Markdown"
            )
        return

    try:
        amount = float(context.args[0])  # Парсим сумму
    except ValueError:
        await message.reply_text(
            "❌ Ошибка! Введите корректную сумму."
        )
        return

    category = " ".join(context.args[1:])  # Склеиваем все оставшиеся слова в категорию
    user_id = update.effective_user.id

    # Добавляем транзакцию через сервис
    transaction = add_new_transaction(user_id, amount, category)

    if transaction:
        # Подтверждение успешного добавления
        await message.reply_text(
            f"✅ Транзакция добавлена:\n💰 {transaction.amount} | 📂 {transaction.category} | 🔹 {transaction.transaction_type}"
        )
    else:
        await message.reply_text(
            "❌ Ошибка при добавлении транзакции. Пожалуйста, попробуйте еще раз."
        )


# Состояния для ConversationHandler
WAITING_FOR_AMOUNT = 1
WAITING_FOR_CATEGORY = 2


async def handle_add_callback(update: Update, context: CallbackContext):
    """Обработчик кнопки ➕ Додати транзакцію (callback_data='add')"""
    await log_command_usage(update, context)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="✍️ *Введите сумму:*\n\n"
                "*Пример:* `500` для сохранения дохода"
                " или `-500` если хотите сохранить расход",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="transactions")
            ]])
        )
        return WAITING_FOR_AMOUNT
    return ConversationHandler.END


async def handle_amount_input(update: Update, context: CallbackContext):
    """Обработка ввода суммы транзакции"""
    user_input = update.message.text

    try:
        amount = float(user_input)
        context.user_data['amount'] = amount

        await update.message.reply_text(
            "✍️ *Введите категорию:*\n\n"
            "*Пример:* `Продукты`, `Транспорт`, `Зарплата`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="transactions")
            ]])
        )
        return WAITING_FOR_CATEGORY
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите корректное число. Попробуйте ещё раз:"
        )
        return WAITING_FOR_AMOUNT


async def handle_category_input(update: Update, context: CallbackContext):
    """Обработка ввода категории транзакции и сохранение в БД"""
    category = update.message.text
    context.user_data['category'] = category

    user_id = update.effective_user.id
    amount = context.user_data.get('amount')

    # Добавляем транзакцию через сервис
    transaction = add_new_transaction(user_id, amount, category)

    if transaction:
        # Подтверждение успешного добавления
        await update.message.reply_text(
            f"✅ Транзакция добавлена:\n💰 {transaction.amount} | 📂 {transaction.category} | 🔹 {transaction.transaction_type}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 К транзакциям", callback_data="transactions")
            ]])
        )
    else:
        await update.message.reply_text(
            "❌ Ошибка при добавлении транзакции. Пожалуйста, попробуйте еще раз.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 К транзакциям", callback_data="transactions")
            ]])
        )

    return ConversationHandler.END


async def history(update: Update, context: CallbackContext):
    """Функция просмотра истории транзакций (последние 10 операций)"""
    await log_command_usage(update, context)

    user_id = None
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        await update.callback_query.answer()  # Закрываем "часики"

    if not user_id:
        return

    # Получаем историю транзакций через сервис
    transactions = get_user_transaction_history(user_id, limit=10)

    if not transactions:
        text = "📜 У вас еще нет транзакций."
    else:
        text = "📝 *История транзакций (последние 10):*\n"
        for transaction in transactions:
            text += f"📅 {transaction.timestamp} | 💰 {transaction.amount} грн | 📂 {transaction.category} ({transaction.transaction_type})\n"

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Назад", callback_data="transactions")
    ]])

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    elif update.message:
        await update.message.reply_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )


async def filter_transactions(update: Update, context: CallbackContext):
    """Функция фильтрации транзакций по категории и типу"""
    await log_command_usage(update, context)

    user_id = update.message.from_user.id
    args = context.args

    if not args:
        await update.message.reply_text("❌ Укажите категорию или тип. Пример: `/transactions Продукты`")
        return

    filter_param = " ".join(args)  # Объединяем аргументы в строку (если фильтр состоит из нескольких слов)

    # Получаем отфильтрованные транзакции через сервис
    transactions = filter_user_transactions(user_id, filter_param)

    if not transactions:
        await update.message.reply_text(f"🔍 Транзакции по фильтру '*{filter_param}*' не найдены.", parse_mode="Markdown")
        return

    message_lines = [f"📂 *Транзакции по фильтру:* `{filter_param}`"]
    for transaction in transactions:
        message_lines.append(f"📅 `{transaction.timestamp}` | 💰 `{transaction.amount} грн` | 🏷️ {transaction.category} ({transaction.transaction_type})")

    message = "\n".join(message_lines)
    await update.message.reply_text(message, parse_mode="Markdown")


async def undo_transaction(update: Update, context: CallbackContext):
    """Функция отмены последней транзакции"""
    await log_command_usage(update, context)

    user_id = None
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        await update.callback_query.answer()

    if not user_id:
        return

    # Получаем последнюю транзакцию через сервис
    transaction = get_user_last_transaction(user_id)

    if not transaction:
        text = "❌ У вас нет транзакций для отмены."
        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data="transactions")
        ]])

        if update.callback_query:
            await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text=text, reply_markup=reply_markup)
        return

    # Удаляем последнюю транзакцию через сервис
    success = delete_user_transaction(transaction.id)

    if success:
        text = f"✅ Последняя транзакция отменена:\n📅 {transaction.timestamp} | 💰 {transaction.amount} грн | 📂 {transaction.category} ({transaction.transaction_type})"
    else:
        text = "❌ Ошибка при отмене транзакции. Пожалуйста, попробуйте еще раз."

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Назад", callback_data="transactions")
    ]])

    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=text, reply_markup=reply_markup)


# Обработчики для транзакций
transactions_handler = CallbackQueryHandler(handle_transactions_callback, pattern='^transactions$')
add_transaction_handler = CommandHandler("add", add_transaction)
history_handler = CommandHandler("history", history)
history_callback_handler = CallbackQueryHandler(history, pattern='^history$')
filter_transactions_handler = CommandHandler("transactions", filter_transactions)
undo_callback_handler = CallbackQueryHandler(undo_transaction, pattern='^undo$')

# ConversationHandler для добавления транзакции через меню
add_transaction_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_add_callback, pattern='^add$')],
    states={
        WAITING_FOR_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_input)],
        WAITING_FOR_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_input)],
    },
    fallbacks=[CallbackQueryHandler(handle_transactions_callback, pattern='^transactions$')]
)
