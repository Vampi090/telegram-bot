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
from services.database_service import save_debt, get_active_debts, get_debt_history, close_debt, get_budgets
from services.transaction_service import add_new_transaction
from datetime import datetime, time

DEBT_NAME, DEBT_AMOUNT, DEBT_TYPE, DEBT_AMOUNT_INPUT, DEBT_NAME_INPUT = range(5)


async def handle_debt_callback(update: Update, context: CallbackContext):
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
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "view_debts":
        debts = get_active_debts(user_id)
        if debts:
            text = "📜 Ваші борги:\n\n"

            debts_i_owe = [(name, amount) for name, amount in debts if amount < 0]
            if debts_i_owe:
                text += "💸 Ви винні:\n"
                for name, amount in debts_i_owe:
                    text += f"• {name}: {abs(amount)}₴\n"
                text += "\n"

            debts_owed_to_me = [(name, amount) for name, amount in debts if amount > 0]
            if debts_owed_to_me:
                text += "💰 Вам винні:\n"
                for name, amount in debts_owed_to_me:
                    text += f"• {name}: {amount}₴\n"
        else:
            text = "✅ У вас немає боргів."
        await query.message.edit_text(text, reply_markup=generate_back_button())

    elif query.data == "debt_history":
        history = get_debt_history(user_id)
        if history:
            text = "<b>📚 Історія боргів:</b>\n\n"

            debts_i_owe = [(name, amount, status, timestamp) for name, amount, status, timestamp in history if
                           amount < 0]
            if debts_i_owe:
                text += "<b>💸 Ви винні:</b>\n"
                for name, amount, status, timestamp in debts_i_owe:
                    text += f"• <b>{name}</b>\n  <code>Сума:</code> <b>{abs(amount)}₴</b>\n  <code>Статус:</code> {status}\n  <code>Дата:</code> {timestamp}\n\n"

            debts_owed_to_me = [(name, amount, status, timestamp) for name, amount, status, timestamp in history if
                                amount > 0]
            if debts_owed_to_me:
                text += "<b>💰 Вам винні:</b>\n"
                for name, amount, status, timestamp in debts_owed_to_me:
                    text += f"• <b>{name}</b>\n  <code>Сума:</code> <b>{amount}₴</b>\n  <code>Статус:</code> {status}\n  <code>Дата:</code> {timestamp}\n\n"
        else:
            text = "Історія порожня."
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=generate_back_button())

    elif query.data == "close_debt":
        text = "<b>📜 Виберіть категорію боргів:</b>"
        keyboard = [
            [InlineKeyboardButton("💸 Ви винні", callback_data="debts_i_owe")],
            [InlineKeyboardButton("💰 Вам винні", callback_data="debts_owed_to_me")],
            [InlineKeyboardButton("🔙 Назад", callback_data="debt_back")]
        ]

        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "add_debt":
        text = "➕ *Додавання боргу*\n\nВиберіть тип боргу:"
        keyboard = [
            [InlineKeyboardButton("💸 Я винен", callback_data="debt_i_owe")],
            [InlineKeyboardButton("💰 Мені винні", callback_data="debt_owed_to_me")],
            [InlineKeyboardButton("🔙 Назад", callback_data="debt_back")]
        ]
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "remind_debt":
        await set_daily_reminder(update, context)
        await query.message.edit_text(
            "🔔 Нагадування встановлено. Ви будете отримувати сповіщення кожного дня о 9:00.",
            reply_markup=generate_back_button()
        )

    elif query.data == "help_debt":
        help_text = (
            "🆘 *Допомога по боргам:*\n\n"
            "➕ Додати борг — додає новий борг із зазначенням типу (я винен/мені винні).\n"
            "💸 Я винен — додає борг, який ви винні комусь.\n"
            "💰 Мені винні — додає борг, який хтось винен вам.\n"
            "📜 Мої борги — список активних боргів.\n"
            "📚 Історія — всі борги, включаючи закриті.\n"
            "✅ Закрити борг — позначити як погашений.\n"
            "🔔 Нагадування — щоденне нагадування о 9:00.\n"
            "🔙 Головне меню — повернення до основного меню."
        )
        await query.message.edit_text(help_text, parse_mode="Markdown", reply_markup=generate_back_button())

    elif query.data == "debt_back":
        await handle_debt_callback(update, context)


async def debt_type_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "debt_i_owe":
        context.user_data["debt_type"] = "i_owe"
        await query.message.edit_text(
            "💸 *Я винен*\n\nВведіть суму боргу:",
            parse_mode="Markdown"
        )
        return DEBT_AMOUNT_INPUT

    elif query.data == "debt_owed_to_me":
        context.user_data["debt_type"] = "owed_to_me"
        await query.message.edit_text(
            "💰 *Мені винні*\n\nВведіть суму боргу:",
            parse_mode="Markdown"
        )
        return DEBT_AMOUNT_INPUT


async def show_debts_by_category(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    debts = get_active_debts(user_id)

    if not debts:
        await query.message.edit_text(
            "✅ У вас немає активних боргів.",
            reply_markup=generate_back_button()
        )
        return

    if query.data == "debts_i_owe":
        debts_i_owe = [(name, amount) for name, amount in debts if amount < 0]

        if not debts_i_owe:
            await query.message.edit_text(
                "✅ У вас немає боргів, які ви винні.",
                reply_markup=generate_back_button()
            )
            return

        text = "<b>📜 Борги, які ви винні:</b>\n\n"
        for i, (name, amount) in enumerate(debts_i_owe):
            text += f"{i + 1}. <b>{name}</b>: {abs(amount)}₴\n"

        keyboard = []

        for i, (name, amount) in enumerate(debts_i_owe):
            row = [
                InlineKeyboardButton(f"💸 Погасити: {name}", callback_data=f"pay_debt_{name}_{abs(amount)}"),
                InlineKeyboardButton(f"Видалити: {name}", callback_data=f"confirm_delete_{name}_{abs(amount)}_i_owe")
            ]
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="close_debt")])

        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "debts_owed_to_me":
        debts_owed_to_me = [(name, amount) for name, amount in debts if amount > 0]

        if not debts_owed_to_me:
            await query.message.edit_text(
                "✅ У вас немає боргів, які вам винні.",
                reply_markup=generate_back_button()
            )
            return

        text = "<b>📜 Борги, які вам винні:</b>\n\n"
        for i, (name, amount) in enumerate(debts_owed_to_me):
            text += f"{i + 1}. <b>{name}</b>: {amount}₴\n"

        keyboard = []

        for i, (name, amount) in enumerate(debts_owed_to_me):
            row = [
                InlineKeyboardButton(f"💰 Борг погашено: {name}", callback_data=f"debt_paid_{name}_{amount}"),
                InlineKeyboardButton(f"Видалити: {name}", callback_data=f"confirm_delete_{name}_{amount}_owed_to_me")
            ]
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="close_debt")])

        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_debt_action(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    callback_data = query.data

    if callback_data.startswith("pay_debt_"):
        parts = callback_data.split("_", 2)
        if len(parts) < 3:
            await query.message.reply_text("❌ Помилка у форматі даних.")
            return

        name_amount = parts[2].rsplit("_", 1)
        if len(name_amount) < 2:
            await query.message.reply_text("❌ Помилка у форматі даних.")
            return

        name = name_amount[0]
        try:
            amount = float(name_amount[1])
        except ValueError:
            await query.message.reply_text("❌ Помилка у форматі суми.")
            return

        budgets = get_budgets(user_id)
        total_budget = sum(budget_amount for _, budget_amount in budgets)

        if total_budget < amount:
            await query.message.edit_text(
                f"❌ Недостатньо коштів у бюджеті для погашення боргу.\n"
                f"Потрібно: {amount}₴\n"
                f"Доступно: {total_budget}₴",
                reply_markup=generate_back_button()
            )
            return

        if close_debt(user_id, name, -amount):
            add_new_transaction(user_id, -amount, "Погашення боргу", "витрата")

            await query.message.edit_text(
                f"✅ Ваш борг {name} на суму {amount}₴ погашено з бюджету.",
                reply_markup=generate_back_button()
            )
        else:
            await query.message.edit_text(
                f"❌ Помилка при погашенні боргу {name}.",
                reply_markup=generate_back_button()
            )

    elif callback_data.startswith("debt_paid_"):
        parts = callback_data.split("_", 2)
        if len(parts) < 3:
            await query.message.reply_text("❌ Помилка у форматі даних.")
            return

        name_amount = parts[2].rsplit("_", 1)
        if len(name_amount) < 2:
            await query.message.reply_text("❌ Помилка у форматі даних.")
            return

        name = name_amount[0]
        try:
            amount = float(name_amount[1])
        except ValueError:
            await query.message.reply_text("❌ Помилка у форматі суми.")
            return

        if close_debt(user_id, name, amount):
            add_new_transaction(user_id, amount, "Повернення боргу", "дохід")

            await query.message.edit_text(
                f"✅ Борг {name} на суму {amount}₴ позначено як погашений. Суму додано до бюджету.",
                reply_markup=generate_back_button()
            )
        else:
            await query.message.edit_text(
                f"❌ Помилка при закритті боргу {name}.",
                reply_markup=generate_back_button()
            )

    elif callback_data.startswith("confirm_delete_"):
        parts = callback_data.split("_", 3)
        if len(parts) < 4:
            await query.message.reply_text("❌ Помилка у форматі даних.")
            return

        name = parts[2]
        try:
            amount = float(parts[3].split("_")[0])
            debt_type = "_".join(parts[3].split("_")[1:])
        except (ValueError, IndexError):
            await query.message.reply_text("❌ Помилка у форматі даних.")
            return

        keyboard = [
            [
                InlineKeyboardButton("✅ Так, видалити", callback_data=f"delete_debt_{name}_{amount}_{debt_type}"),
                InlineKeyboardButton("❌ Ні, скасувати", callback_data=f"cancel_delete_{debt_type}")
            ]
        ]

        await query.message.edit_text(
            f"<b>⚠️ Підтвердження видалення</b>\n\nВи впевнені, що хочете видалити борг <b>{name}</b> на суму <b>{amount}₴</b>?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif callback_data.startswith("cancel_delete_"):
        debt_type = callback_data.split("_", 2)[2]
        await query.message.edit_text(
            "❌ Видалення скасовано.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=f"debts_{debt_type}")]])
        )

    elif callback_data.startswith("delete_debt_"):
        parts = callback_data.split("_", 3)
        if len(parts) < 4:
            await query.message.reply_text("❌ Помилка у форматі даних.")
            return

        name = parts[2]
        try:
            amount = float(parts[3].split("_")[0])
            debt_type = "_".join(parts[3].split("_")[1:])
        except (ValueError, IndexError):
            await query.message.reply_text("❌ Помилка у форматі даних.")
            return

        if debt_type == "i_owe":
            amount = -amount

        if close_debt(user_id, name, amount):
            await query.message.edit_text(
                f"✅ Борг {name} на суму {abs(amount)}₴ видалено з історії.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Назад", callback_data=f"debts_{debt_type}")]])
            )
        else:
            await query.message.edit_text(
                f"❌ Помилка при видаленні боргу {name}.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Назад", callback_data=f"debts_{debt_type}")]])
            )


async def handle_message(update: Update, context: CallbackContext):
    pass


async def ask_debt_name(update: Update, context: CallbackContext):
    await update.message.reply_text("Введіть ім'я людини, якій ви винні або яка винна вам:")
    return DEBT_NAME


async def ask_debt_amount(update: Update, context: CallbackContext):
    context.user_data["debt_name"] = update.message.text
    await update.message.reply_text("Введіть суму боргу:")
    return DEBT_AMOUNT


async def save_debt_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    debt_name = context.user_data.get("debt_name")
    try:
        amount = float(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Введіть коректне число.")
        return DEBT_AMOUNT

    if save_debt(user_id, debt_name, amount):
        await update.message.reply_text(f"✅ Борг збережено: {debt_name} — {amount}₴")
    else:
        await update.message.reply_text("❌ Сталася помилка при збереженні боргу.")

    return ConversationHandler.END


async def cancel_add_debt(update: Update, context: CallbackContext):
    await update.message.reply_text("🚫 Додавання боргу скасовано.")
    return ConversationHandler.END


async def handle_debt_amount_input(update: Update, context: CallbackContext):
    try:
        amount = float(update.message.text)
        context.user_data["debt_amount"] = amount

        await update.message.reply_text(
            "Назва боргу (ПІБ або організація):"
        )
        return DEBT_NAME_INPUT
    except ValueError:
        await update.message.reply_text("❌ Будь ласка, введіть коректне число.")
        return DEBT_AMOUNT_INPUT


async def handle_debt_name_input(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if update.message is None:
        print("Error: update.message is None in handle_debt_name_input")
        return ConversationHandler.END

    debt_name = update.message.text
    debt_amount = context.user_data.get("debt_amount", 0)
    debt_type = context.user_data.get("debt_type", "owed_to_me")

    if not debt_name or debt_name.strip() == "":
        await update.message.reply_text("❌ Назва боргу не може бути порожньою. Спробуйте ще раз.")
        return DEBT_NAME_INPUT

    if debt_type == "i_owe":
        debt_amount = -abs(debt_amount)
    else:
        debt_amount = abs(debt_amount)

    print(f"Saving debt: user_id={user_id}, debt_name='{debt_name}', debt_amount={debt_amount}, debt_type={debt_type}")

    save_result = save_debt(user_id, debt_name, debt_amount)

    print(f"Save result: {save_result}")

    if save_result:
        if debt_type == "i_owe":
            await update.message.reply_text(
                f"✅ Борг збережено: Ви винні {debt_name} — {abs(debt_amount)}₴",
                reply_markup=generate_debt_confirmation_keyboard()
            )
        else:
            await update.message.reply_text(
                f"✅ Борг збережено: {debt_name} винен вам — {debt_amount}₴",
                reply_markup=generate_debt_confirmation_keyboard()
            )
    else:
        await update.message.reply_text("❌ Сталася помилка при збереженні боргу.")

    return ConversationHandler.END


async def send_debt_reminder(context: CallbackContext):
    job = context.job
    user_id = job.chat_id
    debts = get_active_debts(user_id)
    if debts:
        text = "🔔 Нагадування про борги:\n\n"

        debts_i_owe = [(name, amount) for name, amount in debts if amount < 0]
        if debts_i_owe:
            text += "💸 Ви винні:\n"
            for name, amount in debts_i_owe:
                text += f"• {name}: {abs(amount)}₴\n"
            text += "\n"

        debts_owed_to_me = [(name, amount) for name, amount in debts if amount > 0]
        if debts_owed_to_me:
            text += "💰 Вам винні:\n"
            for name, amount in debts_owed_to_me:
                text += f"• {name}: {amount}₴\n"

        await context.bot.send_message(chat_id=user_id, text=text)


async def set_daily_reminder(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    context.job_queue.run_daily(
        send_debt_reminder,
        time=time(hour=9, minute=0),
        chat_id=chat_id,
        name=str(chat_id)
    )

    if update.callback_query:
        await update.callback_query.answer("Нагадування встановлено")
    else:
        await update.message.reply_text("✅ Нагадування будуть приходити кожного дня о 9:00.")


async def adddebt_command(update: Update, context: CallbackContext):
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("❌ Формат: `/adddebt ім'я сума`\nПриклад: `/adddebt Олексій 3000`",
                                            parse_mode="Markdown")
            return

        name = args[0]
        amount = float(args[1])

        if save_debt(update.effective_user.id, name, amount):
            await update.message.reply_text(
                f"✅ Борг додано: {name} — {amount}₴",
                reply_markup=generate_debt_confirmation_keyboard()
            )
        else:
            await update.message.reply_text("❌ Сталася помилка при збереженні боргу.")

    except (ValueError, IndexError):
        await update.message.reply_text("❌ Формат: `/adddebt ім'я сума`\nПриклад: `/adddebt Олексій 3000`",
                                        parse_mode="Markdown")


def generate_back_button():
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="debt_back")]]
    return InlineKeyboardMarkup(keyboard)


def generate_debt_confirmation_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 Повернутися до боргів", callback_data="debt_back")],
        [InlineKeyboardButton("➕ Новий борг", callback_data="add_debt")]
    ]
    return InlineKeyboardMarkup(keyboard)


debt_handler = CallbackQueryHandler(handle_debt_callback, pattern='^debt$')
debt_command_handler = CommandHandler("debt", handle_debt_callback)
debt_menu_handler = CallbackQueryHandler(debt_menu_button_handler,
                                         pattern='^(view_debts|debt_history|close_debt|add_debt|remind_debt|help_debt|debt_back)$')
debt_category_handler = CallbackQueryHandler(show_debts_by_category, pattern='^(debts_i_owe|debts_owed_to_me)$')
debt_action_handler = CallbackQueryHandler(handle_debt_action,
                                           pattern='^(pay_debt_|debt_paid_|delete_debt_|confirm_delete_|cancel_delete_)')
debt_message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
adddebt_handler = CommandHandler("adddebt", adddebt_command)
set_reminder_handler = CommandHandler("debtreminder", set_daily_reminder)

add_debt_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("adddebt_dialog", ask_debt_name),
        CallbackQueryHandler(debt_type_handler, pattern='^(debt_i_owe|debt_owed_to_me)$')
    ],
    states={
        DEBT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_debt_amount)],
        DEBT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_debt_handler)],
        DEBT_AMOUNT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_debt_amount_input)],
        DEBT_NAME_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_debt_name_input)]
    },
    fallbacks=[CommandHandler("cancel", cancel_add_debt)]
)
