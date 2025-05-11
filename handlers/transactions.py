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
from utils.menu_utils import send_or_edit_menu


async def handle_transactions_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)
    user = update.effective_user

    reply_markup = transaction_menu_keyboard()

    await send_or_edit_menu(update, context, "📥 Меню керування транзакціями", reply_markup)


async def add_transaction(update: Update, context: CallbackContext):
    await log_command_usage(update, context)
    message = update.message

    if not message or not context.args:
        if message:
            await send_or_edit_menu(
                update, 
                context, 
                "⚠️ Неверный формат! Используйте: `/add сумма категория`\nПример: `/add 500 еда`", 
                None,
                parse_mode="Markdown"
            )
        return

    try:
        amount = float(context.args[0])
    except ValueError:
        await send_or_edit_menu(
            update, 
            context, 
            "❌ Ошибка! Введите корректную сумму.", 
            None
        )
        return

    category = " ".join(context.args[1:])
    user_id = update.effective_user.id

    transaction = add_new_transaction(user_id, amount, category)

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 К транзакциям", callback_data="transactions")
    ]])

    if transaction:
        text = f"✅ Транзакция добавлена:\n💰 {transaction.amount} | 📂 {transaction.category} | 🔹 {transaction.transaction_type}"
    else:
        text = "❌ Ошибка при добавлении транзакции. Пожалуйста, попробуйте еще раз."
    await send_or_edit_menu(update, context, text, reply_markup)


WAITING_FOR_AMOUNT = 1
WAITING_FOR_CATEGORY = 2


async def handle_add_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    if update.callback_query:
        text = ("✍️ *Введите сумму:*\n\n"
                "*Пример:* `500` для сохранения дохода"
                " или `-500` если хотите сохранить расход")

        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data="transactions")
        ]])

        await send_or_edit_menu(update, context, text, reply_markup, parse_mode="Markdown")
        return WAITING_FOR_AMOUNT
    return ConversationHandler.END


async def handle_amount_input(update: Update, context: CallbackContext):
    user_input = update.message.text

    try:
        amount = float(user_input)
        context.user_data['amount'] = amount

        text = ("✍️ *Введите категорию:*\n\n"
                "*Пример:* `Продукты`, `Транспорт`, `Зарплата`")

        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data="transactions")
        ]])

        await send_or_edit_menu(update, context, text, reply_markup, parse_mode="Markdown")
        return WAITING_FOR_CATEGORY
    except ValueError:
        await send_or_edit_menu(
            update, 
            context, 
            "❌ Пожалуйста, введите корректное число. Попробуйте ещё раз:", 
            None
        )
        return WAITING_FOR_AMOUNT


async def handle_category_input(update: Update, context: CallbackContext):
    category = update.message.text
    context.user_data['category'] = category

    user_id = update.effective_user.id
    amount = context.user_data.get('amount')

    transaction = add_new_transaction(user_id, amount, category)

    if transaction:
        text = f"✅ Транзакция добавлена:\n💰 {transaction.amount} | 📂 {transaction.category} | 🔹 {transaction.transaction_type}"

        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 К транзакциям", callback_data="transactions")
        ]])
        await send_or_edit_menu(update, context, text, reply_markup)
    else:
        text = "❌ Ошибка при добавлении транзакции. Пожалуйста, попробуйте еще раз."

        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 К транзакциям", callback_data="transactions")
        ]])

        await send_or_edit_menu(update, context, text, reply_markup)

    return ConversationHandler.END


async def history(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = None
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        await update.callback_query.answer()

    if not user_id:
        return

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

    await send_or_edit_menu(update, context, text, reply_markup, parse_mode="Markdown")


async def filter_transactions(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.message.from_user.id
    args = context.args

    if not args:
        await send_or_edit_menu(
            update, 
            context, 
            "❌ Укажите категорию или тип. Пример: `/transactions Продукты`", 
            None,
            parse_mode="Markdown"
        )
        return

    filter_param = " ".join(args)

    transactions = filter_user_transactions(user_id, filter_param)

    if not transactions:
        await send_or_edit_menu(
            update, 
            context, 
            f"🔍 Транзакции по фильтру '*{filter_param}*' не найдены.", 
            None,
            parse_mode="Markdown"
        )
        return

    message_lines = [f"📂 *Транзакции по фильтру:* `{filter_param}`"]
    for transaction in transactions:
        message_lines.append(f"📅 `{transaction.timestamp}` | 💰 `{transaction.amount} грн` | 🏷️ {transaction.category} ({transaction.transaction_type})")

    message = "\n".join(message_lines)

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Назад", callback_data="transactions")
    ]])
    await send_or_edit_menu(update, context, message, reply_markup, parse_mode="Markdown")


async def undo_transaction(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = None
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        await update.callback_query.answer()

    if not user_id:
        return

    transaction = get_user_last_transaction(user_id)

    if not transaction:
        text = "❌ У вас нет транзакций для отмены."
        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data="transactions")
        ]])
        await send_or_edit_menu(update, context, text, reply_markup)
        return

    success = delete_user_transaction(transaction.id)

    if success:
        text = f"✅ Последняя транзакция отменена:\n📅 {transaction.timestamp} | 💰 {transaction.amount} грн | 📂 {transaction.category} ({transaction.transaction_type})"
    else:
        text = "❌ Ошибка при отмене транзакции. Пожалуйста, попробуйте еще раз."

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Назад", callback_data="transactions")
    ]])
    await send_or_edit_menu(update, context, text, reply_markup)


transactions_handler = CallbackQueryHandler(handle_transactions_callback, pattern='^transactions$')
add_transaction_handler = CommandHandler("add", add_transaction)
history_handler = CommandHandler("history", history)
history_callback_handler = CallbackQueryHandler(history, pattern='^history$')
filter_transactions_handler = CommandHandler("transactions", filter_transactions)
undo_callback_handler = CallbackQueryHandler(undo_transaction, pattern='^undo$')
add_transaction_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_add_callback, pattern='^add$')],
    states={
        WAITING_FOR_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_input)],
        WAITING_FOR_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_input)],
    },
    fallbacks=[CallbackQueryHandler(handle_transactions_callback, pattern='^transactions$')]
)
