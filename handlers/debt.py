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
from services.database_service import save_debt, get_active_debts, get_debt_history, close_debt, get_budgets, add_reminder
from services.transaction_service import add_new_transaction
from datetime import datetime, time, timedelta
import calendar

DEBT_NAME, DEBT_AMOUNT, DEBT_TYPE, DEBT_AMOUNT_INPUT, DEBT_NAME_INPUT, DEBT_DUE_DATE_INPUT, SELECT_DATE, SELECT_TIME = range(8)


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

            debts_i_owe = [(name, amount, due_date, creation_time) for name, amount, due_date, creation_time in debts if amount < 0]
            if debts_i_owe:
                text += "💸 Ви винні:\n"
                for name, amount, due_date, creation_time in debts_i_owe:
                    text += f"• {name}: {abs(amount)}₴ (до {due_date}, створено: {creation_time})\n"
                text += "\n"

            debts_owed_to_me = [(name, amount, due_date, creation_time) for name, amount, due_date, creation_time in debts if amount > 0]
            if debts_owed_to_me:
                text += "💰 Вам винні:\n"
                for name, amount, due_date, creation_time in debts_owed_to_me:
                    text += f"• {name}: {amount}₴ (до {due_date}, створено: {creation_time})\n"
        else:
            text = "✅ У вас немає боргів."
        await query.message.edit_text(text, reply_markup=generate_back_button())

    elif query.data == "debt_history":
        history = get_debt_history(user_id)
        if history:
            text = "<b>📚 Історія боргів:</b>\n\n"

            debts_i_owe = [(name, amount, status, due_date, creation_time) for name, amount, status, due_date, creation_time in history if
                           amount < 0]
            if debts_i_owe:
                text += "<b>💸 Ви винні:</b>\n"
                for name, amount, status, due_date, creation_time in debts_i_owe:
                    text += f"• <b>{name}</b>\n  <code>Сума:</code> <b>{abs(amount)}₴</b>\n  <code>Статус:</code> {status}\n  <code>Дата закриття:</code> {due_date}\n  <code>Створено:</code> {creation_time}\n\n"

            debts_owed_to_me = [(name, amount, status, due_date, creation_time) for name, amount, status, due_date, creation_time in history if
                                amount > 0]
            if debts_owed_to_me:
                text += "<b>💰 Вам винні:</b>\n"
                for name, amount, status, due_date, creation_time in debts_owed_to_me:
                    text += f"• <b>{name}</b>\n  <code>Сума:</code> <b>{amount}₴</b>\n  <code>Статус:</code> {status}\n  <code>Дата закриття:</code> {due_date}\n  <code>Створено:</code> {creation_time}\n\n"
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
        text = "<b>🔔 Меню нагадувань</b>\n\n"
        text += "Оберіть опцію:"

        keyboard = [
            [InlineKeyboardButton("📅 Встановити нагадування для боргу", callback_data="set_debt_reminder")],
            [InlineKeyboardButton("📋 Переглянути всі нагадування", callback_data="view_all_reminders")],
            [InlineKeyboardButton("🔙 Назад", callback_data="debt_back")]
        ]

        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
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
        debts_i_owe = [(name, amount, due_date, creation_time) for name, amount, due_date, creation_time in debts if amount < 0]

        if not debts_i_owe:
            await query.message.edit_text(
                "✅ У вас немає боргів, які ви винні.",
                reply_markup=generate_back_button()
            )
            return

        text = "<b>📜 Борги, які ви винні:</b>\n\n"
        for i, (name, amount, due_date, creation_time) in enumerate(debts_i_owe):
            text += f"{i + 1}. <b>{name}</b>: {abs(amount)}₴ (до {due_date}, створено: {creation_time})\n"

        keyboard = []

        for i, (name, amount, due_date, creation_time) in enumerate(debts_i_owe):
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
        debts_owed_to_me = [(name, amount, due_date, creation_time) for name, amount, due_date, creation_time in debts if amount > 0]

        if not debts_owed_to_me:
            await query.message.edit_text(
                "✅ У вас немає боргів, які вам винні.",
                reply_markup=generate_back_button()
            )
            return

        text = "<b>📜 Борги, які вам винні:</b>\n\n"
        for i, (name, amount, due_date, creation_time) in enumerate(debts_owed_to_me):
            text += f"{i + 1}. <b>{name}</b>: {amount}₴ (до {due_date}, створено: {creation_time})\n"

        keyboard = []

        for i, (name, amount, due_date, creation_time) in enumerate(debts_owed_to_me):
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


async def handle_debt_reminder_options(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    callback_data = query.data

    # Handle set_debt_reminder callback
    if callback_data == "set_debt_reminder":
        debts = get_active_debts(user_id)
        if not debts:
            await query.message.edit_text(
                "✅ У вас немає активних боргів для нагадування.",
                reply_markup=generate_back_button()
            )
            return

        text = "<b>🔔 Виберіть борг для нагадування:</b>\n\n"

        keyboard = []

        debts_i_owe = [(name, amount, due_date, creation_time) for name, amount, due_date, creation_time in debts if amount < 0]
        if debts_i_owe:
            text += "<b>💸 Ви винні:</b>\n"
            for i, (name, amount, due_date, creation_time) in enumerate(debts_i_owe):
                text += f"{i + 1}. <b>{name}</b>: {abs(amount)}₴ (до {due_date})\n"
                keyboard.append([InlineKeyboardButton(f"💸 {name}: {abs(amount)}₴", 
                                                    callback_data=f"debt_reminder_{name}_{abs(amount)}_i_owe")])
            text += "\n"

        debts_owed_to_me = [(name, amount, due_date, creation_time) for name, amount, due_date, creation_time in debts if amount > 0]
        if debts_owed_to_me:
            text += "<b>💰 Вам винні:</b>\n"
            for i, (name, amount, due_date, creation_time) in enumerate(debts_owed_to_me):
                text += f"{i + 1}. <b>{name}</b>: {amount}₴ (до {due_date})\n"
                keyboard.append([InlineKeyboardButton(f"💰 {name}: {amount}₴", 
                                                    callback_data=f"debt_reminder_{name}_{amount}_owed_to_me")])

        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="remind_debt")])

        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Handle view_all_reminders callback
    elif callback_data == "view_all_reminders":
        from handlers.reminders import handle_list_reminders
        # Store the return path to come back to debt menu
        context.user_data['return_to_debt_menu'] = True
        await handle_list_reminders(update, context)
        return

    # Handle reminder option selection
    if callback_data.startswith("debt_reminder_option_"):
        option = callback_data.split("_")[-1]

        name = context.user_data.get('debt_reminder_name')
        amount = context.user_data.get('debt_reminder_amount')
        debt_type = context.user_data.get('debt_reminder_type')
        due_date = context.user_data.get('debt_reminder_due_date')

        if not all([name, amount, debt_type, due_date]):
            await query.message.edit_text("❌ Помилка: відсутні дані про борг.", reply_markup=generate_back_button())
            return

        debt_type_text = "Ви винні" if debt_type == "i_owe" else "Вам винні"

        if option == "one_day":
            reminder_date = context.user_data.get('debt_reminder_one_day_before')
            reminder_time = "09:00:00"
            reminder_datetime = f"{reminder_date} {reminder_time}"

            title = f"Борг {name}: {amount}₴ ({debt_type_text}) - завтра термін оплати!"
            reminder_id = add_reminder(user_id, title, reminder_datetime)

            if reminder_id:
                await query.message.edit_text(
                    f"✅ Нагадування встановлено на {reminder_date} о 09:00.\n\nБорг: {name}, {amount}₴ ({debt_type_text})\nТермін оплати: {due_date}",
                    reply_markup=generate_back_button()
                )
            else:
                await query.message.edit_text(
                    "❌ Помилка при створенні нагадування.",
                    reply_markup=generate_back_button()
                )

        elif option == "one_week":
            reminder_date = context.user_data.get('debt_reminder_one_week_before')
            reminder_time = "09:00:00"
            reminder_datetime = f"{reminder_date} {reminder_time}"

            title = f"Борг {name}: {amount}₴ ({debt_type_text}) - через тиждень термін оплати!"
            reminder_id = add_reminder(user_id, title, reminder_datetime)

            if reminder_id:
                await query.message.edit_text(
                    f"✅ Нагадування встановлено на {reminder_date} о 09:00.\n\nБорг: {name}, {amount}₴ ({debt_type_text})\nТермін оплати: {due_date}",
                    reply_markup=generate_back_button()
                )
            else:
                await query.message.edit_text(
                    "❌ Помилка при створенні нагадування.",
                    reply_markup=generate_back_button()
                )

        elif option == "custom":
            # Initialize date selection for custom reminder
            context.user_data['debt_reminder_custom'] = True

            # Set initial date to today
            now = datetime.now()
            context.user_data['reminder_year'] = now.year
            context.user_data['reminder_month'] = now.month
            context.user_data['reminder_day'] = now.day

            keyboard = generate_date_selection_keyboard(context)
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.edit_text(
                f"Борг: <b>{name}</b>: {amount}₴ ({debt_type_text})\nТермін оплати: {due_date}\n\nОберіть дату нагадування:",
                parse_mode="HTML",
                reply_markup=reply_markup
            )

            return SELECT_DATE

        return

    # Handle initial debt selection for reminder
    if not callback_data.startswith("debt_reminder_"):
        return

    # Get the debt information from active debts instead of parsing the callback data
    debts = get_active_debts(user_id)

    # Extract the debt name from the callback data - everything between "debt_reminder_" and the last two underscores
    callback_parts = callback_data.split("_")
    if len(callback_parts) < 4:  # At minimum: debt_reminder_name_type
        await query.message.edit_text("❌ Помилка у форматі даних.", reply_markup=generate_back_button())
        return

    # The last part is the debt type (i_owe or owed_to_me)
    debt_type = callback_parts[-1]
    if debt_type not in ["i_owe", "owed_to_me"]:
        debt_type = callback_parts[-2] + "_" + callback_parts[-1]  # Handle "owed_to_me" which has an underscore

    # The second to last part is the amount
    try:
        amount = float(callback_parts[-2])
        # If debt_type contains "owed_to_me", then we need to adjust our parsing
        if "owed_to_me" in debt_type:
            amount = float(callback_parts[-3])
            debt_type = "owed_to_me"
    except (ValueError, IndexError):
        # Instead of showing an error, let's find the debt in the active debts
        found_debt = False
        for debt_name, debt_amount, debt_due_date, _ in debts:
            # Try to match the debt by checking if its name is in the callback data
            if debt_name in callback_data:
                if (debt_type == "i_owe" and debt_amount < 0) or (debt_type == "owed_to_me" and debt_amount > 0):
                    name = debt_name
                    amount = abs(debt_amount)
                    found_debt = True
                    break

        if not found_debt:
            await query.message.edit_text("❌ Не вдалося знайти борг.", reply_markup=generate_back_button())
            return

    # Get the name by removing the prefix, amount, and type from the callback data
    name_prefix = "debt_reminder_"
    name_suffix = f"_{amount}_{debt_type}"
    if callback_data.startswith(name_prefix) and name_suffix in callback_data:
        name = callback_data[len(name_prefix):callback_data.rfind(name_suffix)]
    else:
        # If we can't extract the name from the callback data, try to find it in the active debts
        found_debt = False
        for debt_name, debt_amount, debt_due_date, _ in debts:
            if (debt_type == "i_owe" and debt_amount < 0 and abs(debt_amount) == amount) or \
               (debt_type == "owed_to_me" and debt_amount > 0 and debt_amount == amount):
                name = debt_name
                found_debt = True
                break

        if not found_debt:
            await query.message.edit_text("❌ Не вдалося знайти борг.", reply_markup=generate_back_button())
            return

    # Store debt info in context for later use
    context.user_data['debt_reminder_name'] = name
    context.user_data['debt_reminder_amount'] = amount
    context.user_data['debt_reminder_type'] = debt_type

    # Get the due date for this debt
    debts = get_active_debts(user_id)
    due_date = None

    for debt_name, debt_amount, debt_due_date, _ in debts:
        if debt_name == name:
            if (debt_type == "i_owe" and debt_amount < 0) or (debt_type == "owed_to_me" and debt_amount > 0):
                due_date = debt_due_date
                break

    if not due_date:
        await query.message.edit_text("❌ Не вдалося знайти дату закриття боргу.", reply_markup=generate_back_button())
        return

    context.user_data['debt_reminder_due_date'] = due_date

    # Calculate dates for reminder options
    try:
        due_date_obj = datetime.strptime(due_date, '%Y-%m-%d')
        one_day_before = (due_date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
        one_week_before = (due_date_obj - timedelta(days=7)).strftime('%Y-%m-%d')

        context.user_data['debt_reminder_one_day_before'] = one_day_before
        context.user_data['debt_reminder_one_week_before'] = one_week_before
    except ValueError:
        await query.message.edit_text("❌ Помилка у форматі дати закриття боргу.", reply_markup=generate_back_button())
        return

    # Show reminder options
    debt_type_text = "Ви винні" if debt_type == "i_owe" else "Вам винні"
    text = f"<b>🔔 Нагадування для боргу:</b>\n\n<b>{name}</b>: {amount}₴ ({debt_type_text})\nДата закриття: {due_date}\n\n<b>Виберіть варіант нагадування:</b>"

    keyboard = [
        [InlineKeyboardButton("📅 За день до закриття", callback_data=f"debt_reminder_option_one_day")],
        [InlineKeyboardButton("📆 За тиждень до закриття", callback_data=f"debt_reminder_option_one_week")],
        [InlineKeyboardButton("🗓 Обрати свою дату", callback_data=f"debt_reminder_option_custom")],
        [InlineKeyboardButton("🔙 Назад", callback_data="set_debt_reminder")]
    ]

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

    context.user_data["debt_name"] = debt_name
    context.user_data["debt_amount_final"] = debt_amount

    debt_type_text = "Ви винні" if debt_type == "i_owe" else "Вам винні"

    keyboard = generate_date_selection_keyboard(context)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Борг: *{debt_name}* ({debt_type_text})\n\nОберіть дату, до якої потрібно закрити борг:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    return SELECT_DATE


def generate_time_selection_keyboard(context):
    hour = context.user_data.get('reminder_hour', 9)
    minute = context.user_data.get('reminder_minute', 0)

    keyboard = []

    keyboard.append([InlineKeyboardButton("🕐 Години", callback_data="ignore")])

    hours_row = []
    for h in range(0, 24, 4):
        hours_row = []
        for i in range(4):
            if h + i < 24:
                button_text = f"{h + i:02d}" + ("✓" if h + i == hour else "")
                hours_row.append(InlineKeyboardButton(button_text, callback_data=f"hour_{h + i}"))
        keyboard.append(hours_row)

    keyboard.append([InlineKeyboardButton("⏱ Хвилини", callback_data="ignore")])

    for row_start in range(0, 60, 20):
        minutes_row = []
        for m in range(row_start, min(row_start + 20, 60), 5):
            button_text = f"{m:02d}" + ("✓" if m == minute else "")
            minutes_row.append(InlineKeyboardButton(button_text, callback_data=f"minute_{m}"))
        keyboard.append(minutes_row)

    keyboard.append([InlineKeyboardButton("💾 Зберегти нагадування", callback_data="save_reminder")])
    keyboard.append([InlineKeyboardButton("🔙 Назад до вибору дати", callback_data="back_to_date")])

    return keyboard


async def handle_time_selection(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    query = update.callback_query
    await query.answer()

    callback_data = query.data
    user_id = query.from_user.id

    if callback_data.startswith("hour_"):
        hour = int(callback_data.split("_")[1])
        context.user_data['reminder_hour'] = hour

        keyboard = generate_time_selection_keyboard(context)
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_reply_markup(reply_markup=reply_markup)
        return SELECT_TIME

    elif callback_data.startswith("minute_"):
        minute = int(callback_data.split("_")[1])
        context.user_data['reminder_minute'] = minute

        keyboard = generate_time_selection_keyboard(context)
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_reply_markup(reply_markup=reply_markup)
        return SELECT_TIME

    elif callback_data == "back_to_date":
        keyboard = generate_date_selection_keyboard(context)
        reply_markup = InlineKeyboardMarkup(keyboard)

        name = context.user_data.get('debt_reminder_name')
        amount = context.user_data.get('debt_reminder_amount')
        debt_type = context.user_data.get('debt_reminder_type')
        debt_type_text = "Ви винні" if debt_type == "i_owe" else "Вам винні"
        due_date = context.user_data.get('debt_reminder_due_date')

        await query.edit_message_text(
            text=f"Борг: <b>{name}</b>: {amount}₴ ({debt_type_text})\nТермін оплати: {due_date}\n\nОберіть дату нагадування:",
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        return SELECT_DATE

    elif callback_data == "save_reminder":
        name = context.user_data.get('debt_reminder_name')
        amount = context.user_data.get('debt_reminder_amount')
        debt_type = context.user_data.get('debt_reminder_type')
        debt_type_text = "Ви винні" if debt_type == "i_owe" else "Вам винні"
        due_date = context.user_data.get('debt_reminder_due_date')

        year = context.user_data.get('reminder_year')
        month = context.user_data.get('reminder_month')
        day = context.user_data.get('reminder_day')
        hour = context.user_data.get('reminder_hour', 9)
        minute = context.user_data.get('reminder_minute', 0)

        # Check if all required values are set
        if not all([year, month, day]):
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_date")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                text="❌ Будь ласка, оберіть дату нагадування.",
                reply_markup=reply_markup
            )
            return SELECT_TIME

        try:
            reminder_datetime = datetime(year, month, day, hour, minute)
            reminder_datetime_str = reminder_datetime.strftime("%Y-%m-%d %H:%M:%S")

            if reminder_datetime <= datetime.now():
                keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_date")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    text="❌ Дата та час нагадування мають бути в майбутньому. Будь ласка, оберіть іншу дату або час.",
                    reply_markup=reply_markup
                )
                return SELECT_TIME

            title = f"Борг {name}: {amount}₴ ({debt_type_text}) - нагадування про оплату!"
            reminder_id = add_reminder(user_id, title, reminder_datetime_str)

            if reminder_id:
                formatted_date = reminder_datetime.strftime("%d.%m.%Y %H:%M")
                await query.edit_message_text(
                    f"✅ Нагадування встановлено на {formatted_date}.\n\nБорг: {name}, {amount}₴ ({debt_type_text})\nТермін оплати: {due_date}",
                    reply_markup=generate_back_button()
                )
            else:
                await query.edit_message_text(
                    "❌ Помилка при створенні нагадування.",
                    reply_markup=generate_back_button()
                )

            # Clear debt reminder data
            for key in list(context.user_data.keys()):
                if key.startswith('debt_reminder_') or key.startswith('reminder_'):
                    del context.user_data[key]

            return ConversationHandler.END

        except (ValueError, TypeError) as e:
            print(f"Error creating reminder: {e}")
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_date")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                text=f"❌ Помилка при створенні нагадування: {e}",
                reply_markup=reply_markup
            )
            return SELECT_TIME

    return SELECT_TIME


def generate_date_selection_keyboard(context):
    # Check if this is a debt reminder or regular debt
    is_debt_reminder = context.user_data.get('debt_reminder_custom', False)

    if is_debt_reminder:
        year = context.user_data.get('reminder_year', datetime.now().year)
        month = context.user_data.get('reminder_month', datetime.now().month)
    else:
        year = context.user_data.get('debt_year', datetime.now().year)
        month = context.user_data.get('debt_month', datetime.now().month)

    now = datetime.now()

    keyboard = []

    month_names = [
        "Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
        "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"
    ]
    month_name = month_names[month - 1]

    nav_row = []

    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1
    nav_row.append(InlineKeyboardButton("◀️", callback_data=f"date_prev_{prev_year}_{prev_month}"))

    nav_row.append(InlineKeyboardButton(f"{month_name} {year}", callback_data="ignore"))

    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1
    nav_row.append(InlineKeyboardButton("▶️", callback_data=f"date_next_{next_year}_{next_month}"))

    keyboard.append(nav_row)

    days_of_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
    keyboard.append([InlineKeyboardButton(day, callback_data="ignore") for day in days_of_week])

    first_day, num_days = calendar.monthrange(year, month)

    day = 1
    for week in range(6):
        week_buttons = []
        for weekday in range(7):
            if week == 0 and weekday < first_day:
                week_buttons.append(InlineKeyboardButton(" ", callback_data="ignore"))
            elif day > num_days:
                week_buttons.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                is_past = False
                if year < now.year or (year == now.year and month < now.month) or (
                        year == now.year and month == now.month and day < now.day):
                    is_past = True

                # Check the appropriate day variable based on whether it's a debt reminder or a regular debt
                if is_debt_reminder:
                    is_selected = day == context.user_data.get('reminder_day', 0)
                else:
                    is_selected = day == context.user_data.get('debt_day', 0)

                button_text = str(day)
                if is_selected:
                    button_text = f"✓{day}"

                callback_data = f"date_{year}_{month}_{day}" if not is_past else "ignore"

                week_buttons.append(InlineKeyboardButton(button_text, callback_data=callback_data))

                day += 1

        if any(button.text.strip() != "" for button in week_buttons):
            keyboard.append(week_buttons)

    # Different button for debt reminder vs regular debt
    is_debt_reminder = context.user_data.get('debt_reminder_custom', False)
    if is_debt_reminder:
        keyboard.append([InlineKeyboardButton("⏰ Обрати час", callback_data="select_time")])
    else:
        keyboard.append([InlineKeyboardButton("💾 Зберегти дату", callback_data="save_debt_date")])

    return keyboard


async def handle_date_selection(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    query = update.callback_query
    await query.answer()

    callback_data = query.data

    # Check if this is a debt reminder custom date selection
    is_debt_reminder = context.user_data.get('debt_reminder_custom', False)

    if callback_data.startswith("date_prev_") or callback_data.startswith("date_next_"):
        parts = callback_data.split("_")
        year = int(parts[2])
        month = int(parts[3])

        if is_debt_reminder:
            context.user_data['reminder_year'] = year
            context.user_data['reminder_month'] = month
        else:
            context.user_data['debt_year'] = year
            context.user_data['debt_month'] = month

        keyboard = generate_date_selection_keyboard(context)
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_reply_markup(reply_markup=reply_markup)
        return SELECT_DATE

    elif callback_data.startswith("date_"):
        parts = callback_data.split("_")
        year = int(parts[1])
        month = int(parts[2])
        day = int(parts[3])

        if is_debt_reminder:
            context.user_data['reminder_year'] = year
            context.user_data['reminder_month'] = month
            context.user_data['reminder_day'] = day
        else:
            context.user_data['debt_year'] = year
            context.user_data['debt_month'] = month
            context.user_data['debt_day'] = day

        keyboard = generate_date_selection_keyboard(context)
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_reply_markup(reply_markup=reply_markup)
        return SELECT_DATE

    elif callback_data == "select_time" and is_debt_reminder:
        # Handle time selection for debt reminder
        keyboard = generate_time_selection_keyboard(context)
        reply_markup = InlineKeyboardMarkup(keyboard)

        name = context.user_data.get('debt_reminder_name')
        amount = context.user_data.get('debt_reminder_amount')
        debt_type = context.user_data.get('debt_reminder_type')
        debt_type_text = "Ви винні" if debt_type == "i_owe" else "Вам винні"
        due_date = context.user_data.get('debt_reminder_due_date')

        year = context.user_data.get('reminder_year')
        month = context.user_data.get('reminder_month')
        day = context.user_data.get('reminder_day')

        date_str = f"{day:02d}.{month:02d}.{year}"

        await query.edit_message_text(
            text=f"Борг: <b>{name}</b>: {amount}₴ ({debt_type_text})\nТермін оплати: {due_date}\n\nДата нагадування: <b>{date_str}</b>\n\nОберіть час нагадування:",
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        return SELECT_TIME

    elif callback_data == "save_debt_date":
        user_id = query.from_user.id
        year = context.user_data.get('debt_year')
        month = context.user_data.get('debt_month')
        day = context.user_data.get('debt_day')

        if not all([year, month, day]):
            keyboard = generate_date_selection_keyboard(context)
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                text="❌ Будь ласка, оберіть дату закриття боргу.",
                reply_markup=reply_markup
            )
            return SELECT_DATE

        debt_name = context.user_data.get("debt_name", "")
        debt_amount = context.user_data.get("debt_amount_final", 0)
        debt_type = context.user_data.get("debt_type", "owed_to_me")

        due_date = f"{year}-{month:02d}-{day:02d}"

        print(f"Saving debt: user_id={user_id}, debt_name='{debt_name}', debt_amount={debt_amount}, debt_type={debt_type}, due_date={due_date}")

        save_result = save_debt(user_id, debt_name, debt_amount, due_date)

        print(f"Save result: {save_result}")

        if save_result:
            if debt_type == "i_owe":
                await query.edit_message_text(
                    f"✅ Борг збережено: Ви винні {debt_name} — {abs(debt_amount)}₴\nДата закриття: {due_date}",
                    reply_markup=generate_debt_confirmation_keyboard()
                )
            else:
                await query.edit_message_text(
                    f"✅ Борг збережено: {debt_name} винен вам — {debt_amount}₴\nДата закриття: {due_date}",
                    reply_markup=generate_debt_confirmation_keyboard()
                )
        else:
            await query.edit_message_text(
                "❌ Сталася помилка при збереженні боргу.",
                reply_markup=generate_back_button()
            )

        return ConversationHandler.END

    return SELECT_DATE


async def handle_debt_due_date_input(update: Update, context: CallbackContext):
    # This function is kept for backward compatibility but now redirects to the date selection
    debt_name = context.user_data.get("debt_name", "")
    debt_type = context.user_data.get("debt_type", "owed_to_me")

    debt_type_text = "Ви винні" if debt_type == "i_owe" else "Вам винні"

    keyboard = generate_date_selection_keyboard(context)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Борг: *{debt_name}* ({debt_type_text})\n\nОберіть дату, до якої потрібно закрити борг:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    return SELECT_DATE


async def send_debt_reminder(context: CallbackContext):
    job = context.job
    user_id = job.chat_id
    debts = get_active_debts(user_id)
    if debts:
        text = "🔔 Нагадування про борги:\n\n"

        debts_i_owe = [(name, amount, due_date, creation_time) for name, amount, due_date, creation_time in debts if amount < 0]
        if debts_i_owe:
            text += "💸 Ви винні:\n"
            for name, amount, due_date, creation_time in debts_i_owe:
                text += f"• {name}: {abs(amount)}₴ (до {due_date}, створено: {creation_time})\n"
            text += "\n"

        debts_owed_to_me = [(name, amount, due_date, creation_time) for name, amount, due_date, creation_time in debts if amount > 0]
        if debts_owed_to_me:
            text += "💰 Вам винні:\n"
            for name, amount, due_date, creation_time in debts_owed_to_me:
                text += f"• {name}: {amount}₴ (до {due_date}, створено: {creation_time})\n"

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
            await update.message.reply_text("❌ Формат: `/adddebt ім'я сума [дата]`\nПриклад: `/adddebt Олексій 3000 2023-12-31`",
                                            parse_mode="Markdown")
            return

        name = args[0]
        amount = float(args[1])
        due_date = args[2] if len(args) > 2 else None

        if due_date:
            try:
                # Validate date format
                datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                await update.message.reply_text("❌ Неправильний формат дати. Використовуйте формат РРРР-ММ-ДД (наприклад, 2023-12-31).")
                return

        if save_debt(update.effective_user.id, name, amount, due_date):
            due_date_text = f" (до {due_date})" if due_date else ""
            await update.message.reply_text(
                f"✅ Борг додано: {name} — {amount}₴{due_date_text}",
                reply_markup=generate_debt_confirmation_keyboard()
            )
        else:
            await update.message.reply_text("❌ Сталася помилка при збереженні боргу.")

    except (ValueError, IndexError):
        await update.message.reply_text("❌ Формат: `/adddebt ім'я сума [дата]`\nПриклад: `/adddebt Олексій 3000 2023-12-31`",
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
debt_reminder_handler = CallbackQueryHandler(handle_debt_reminder_options,
                                           pattern='^(debt_reminder_|debt_reminder_option_)')
debt_message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
adddebt_handler = CommandHandler("adddebt", adddebt_command)
set_reminder_handler = CommandHandler("debtreminder", set_daily_reminder)
date_selection_handler = CallbackQueryHandler(handle_date_selection, 
                                             pattern='^(date_|save_debt_date|ignore|select_time)') 
time_selection_handler = CallbackQueryHandler(handle_time_selection,
                                             pattern='^(hour_|minute_|save_reminder|back_to_date)')

# Conversation handler for debt reminders
debt_reminder_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(handle_debt_reminder_options, pattern='^debt_reminder_option_custom$')
    ],
    states={
        SELECT_DATE: [
            CallbackQueryHandler(handle_date_selection, pattern='^(date_|select_time|ignore)')
        ],
        SELECT_TIME: [
            CallbackQueryHandler(handle_time_selection, pattern='^(hour_|minute_|back_to_date|save_reminder)')
        ]
    },
    fallbacks=[
        CallbackQueryHandler(handle_debt_callback, pattern='^debt_back$'),
        CallbackQueryHandler(handle_debt_reminder_options, pattern='^remind_debt$')
    ],
    name="debt_reminder",
    persistent=False
)

add_debt_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("adddebt_dialog", ask_debt_name),
        CallbackQueryHandler(debt_type_handler, pattern='^(debt_i_owe|debt_owed_to_me)$')
    ],
    states={
        DEBT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_debt_amount)],
        DEBT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_debt_handler)],
        DEBT_AMOUNT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_debt_amount_input)],
        DEBT_NAME_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_debt_name_input)],
        DEBT_DUE_DATE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_debt_due_date_input)],
        SELECT_DATE: [date_selection_handler],
        SELECT_TIME: [time_selection_handler]
    },
    fallbacks=[CommandHandler("cancel", cancel_add_debt)]
)
