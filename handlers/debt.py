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

# Состояния для ConversationHandler
DEBT_NAME, DEBT_AMOUNT, DEBT_TYPE, DEBT_AMOUNT_INPUT, DEBT_NAME_INPUT = range(5)


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
        if debts:
            text = "📜 Ваши долги:\n\n"

            # Долги, которые пользователь должен другим
            debts_i_owe = [(name, amount) for name, amount in debts if amount < 0]
            if debts_i_owe:
                text += "💸 Вы должны:\n"
                for name, amount in debts_i_owe:
                    text += f"• {name}: {abs(amount)}₴\n"
                text += "\n"

            # Долги, которые должны пользователю
            debts_owed_to_me = [(name, amount) for name, amount in debts if amount > 0]
            if debts_owed_to_me:
                text += "💰 Вам должны:\n"
                for name, amount in debts_owed_to_me:
                    text += f"• {name}: {amount}₴\n"
        else:
            text = "✅ У вас нет долгов."
        await query.message.edit_text(text, reply_markup=generate_back_button())

    elif query.data == "debt_history":
        history = get_debt_history(user_id)
        if history:
            text = "<b>📚 История долгов:</b>\n\n"

            # Долги, которые пользователь должен другим
            debts_i_owe = [(name, amount, status, timestamp) for name, amount, status, timestamp in history if amount < 0]
            if debts_i_owe:
                text += "<b>💸 Вы должны:</b>\n"
                for name, amount, status, timestamp in debts_i_owe:
                    # Используем индикатор со знаком минус для долгов, которые пользователь должен
                    text += f"• <b>{name}</b>\n  <code>Сумма:</code> <b>{abs(amount)}₴</b>\n  <code>Статус:</code> {status}\n  <code>Дата:</code> {timestamp}\n\n"

            # Долги, которые должны пользователю
            debts_owed_to_me = [(name, amount, status, timestamp) for name, amount, status, timestamp in history if amount > 0]
            if debts_owed_to_me:
                text += "<b>💰 Вам должны:</b>\n"
                for name, amount, status, timestamp in debts_owed_to_me:
                    # Используем индикатор со знаком плюс для долгов, которые должны пользователю
                    text += f"• <b>{name}</b>\n  <code>Сумма:</code> <b>{amount}₴</b>\n  <code>Статус:</code> {status}\n  <code>Дата:</code> {timestamp}\n\n"
        else:
            text = "История пуста."
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=generate_back_button())

    elif query.data == "close_debt":
        # Показываем две кнопки для выбора категории долгов
        text = "<b>📜 Выберите категорию долгов:</b>"
        keyboard = [
            [InlineKeyboardButton("💸 Вы должны", callback_data="debts_i_owe")],
            [InlineKeyboardButton("💰 Вам должны", callback_data="debts_owed_to_me")],
            [InlineKeyboardButton("🔙 Назад", callback_data="debt_back")]
        ]

        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "add_debt":
        text = "➕ *Добавление долга*\n\nВыберите тип долга:"
        keyboard = [
            [InlineKeyboardButton("💸 Я должен", callback_data="debt_i_owe")],
            [InlineKeyboardButton("💰 Мне должны", callback_data="debt_owed_to_me")],
            [InlineKeyboardButton("🔙 Назад", callback_data="debt_back")]
        ]
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "remind_debt":
        await set_daily_reminder(update, context)
        await query.message.edit_text(
            "🔔 Напоминание установлено. Вы будете получать уведомления каждый день в 9:00.",
            reply_markup=generate_back_button()
        )

    elif query.data == "help_debt":
        help_text = (
            "🆘 *Помощь по долгам:*\n\n"
            "➕ Добавить долг — добавляет новый долг с указанием типа (я должен/мне должны).\n"
            "💸 Я должен — добавляет долг, который вы должны кому-то.\n"
            "💰 Мне должны — добавляет долг, который кто-то должен вам.\n"
            "📜 Мои долги — список активных долгов.\n"
            "📚 История — все долги, включая закрытые.\n"
            "✅ Закрыть долг — отметить как погашенный.\n"
            "🔔 Напоминание — ежедневное напоминание в 9:00.\n"
            "🔙 Главное меню — возврат в основное меню."
        )
        await query.message.edit_text(help_text, parse_mode="Markdown", reply_markup=generate_back_button())

    elif query.data == "debt_back":
        await handle_debt_callback(update, context)


async def debt_type_handler(update: Update, context: CallbackContext):
    """Обработчик выбора типа долга"""
    query = update.callback_query
    await query.answer()

    if query.data == "debt_i_owe":
        # Пользователь выбрал "Я должен"
        context.user_data["debt_type"] = "i_owe"
        await query.message.edit_text(
            "💸 *Я должен*\n\nВведите сумму долга:", 
            parse_mode="Markdown"
        )
        return DEBT_AMOUNT_INPUT

    elif query.data == "debt_owed_to_me":
        # Пользователь выбрал "Мне должны"
        context.user_data["debt_type"] = "owed_to_me"
        await query.message.edit_text(
            "💰 *Мне должны*\n\nВведите сумму долга:", 
            parse_mode="Markdown"
        )
        return DEBT_AMOUNT_INPUT


async def show_debts_by_category(update: Update, context: CallbackContext):
    """Обработчик для отображения долгов по категориям (я должен/мне должны)"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    debts = get_active_debts(user_id)

    if not debts:
        await query.message.edit_text(
            "✅ У вас нет активных долгов.",
            reply_markup=generate_back_button()
        )
        return

    if query.data == "debts_i_owe":
        # Показываем долги, которые пользователь должен другим
        debts_i_owe = [(name, amount) for name, amount in debts if amount < 0]

        if not debts_i_owe:
            await query.message.edit_text(
                "✅ У вас нет долгов, которые вы должны.",
                reply_markup=generate_back_button()
            )
            return

        text = "<b>📜 Долги, которые вы должны:</b>\n\n"
        for i, (name, amount) in enumerate(debts_i_owe):
            text += f"{i+1}. <b>{name}</b>: {abs(amount)}₴\n"

        # Создаем клавиатуру с кнопками для каждого долга
        keyboard = []

        # Кнопки для долгов, которые пользователь должен
        for i, (name, amount) in enumerate(debts_i_owe):
            row = [
                InlineKeyboardButton(f"💸 Погасить: {name}", callback_data=f"pay_debt_{name}_{abs(amount)}"),
                InlineKeyboardButton(f"Удалить: {name}", callback_data=f"confirm_delete_{name}_{abs(amount)}_i_owe")
            ]
            keyboard.append(row)

        # Добавляем кнопку "Назад"
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="close_debt")])

        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "debts_owed_to_me":
        # Показываем долги, которые должны пользователю
        debts_owed_to_me = [(name, amount) for name, amount in debts if amount > 0]

        if not debts_owed_to_me:
            await query.message.edit_text(
                "✅ У вас нет долгов, которые вам должны.",
                reply_markup=generate_back_button()
            )
            return

        text = "<b>📜 Долги, которые вам должны:</b>\n\n"
        for i, (name, amount) in enumerate(debts_owed_to_me):
            text += f"{i+1}. <b>{name}</b>: {amount}₴\n"

        # Создаем клавиатуру с кнопками для каждого долга
        keyboard = []

        # Кнопки для долгов, которые должны пользователю
        for i, (name, amount) in enumerate(debts_owed_to_me):
            row = [
                InlineKeyboardButton(f"💰 Долг погашен: {name}", callback_data=f"debt_paid_{name}_{amount}"),
                InlineKeyboardButton(f"Удалить: {name}", callback_data=f"confirm_delete_{name}_{amount}_owed_to_me")
            ]
            keyboard.append(row)

        # Добавляем кнопку "Назад"
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="close_debt")])

        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_debt_action(update: Update, context: CallbackContext):
    """Обработчик действий с долгами (погашение, удаление)"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    callback_data = query.data

    # Обработка кнопки "Погасить долг"
    if callback_data.startswith("pay_debt_"):
        # Извлекаем имя и сумму из callback_data
        parts = callback_data.split("_", 2)
        if len(parts) < 3:
            await query.message.reply_text("❌ Ошибка в формате данных.")
            return

        # Формат: pay_debt_name_amount
        name_amount = parts[2].rsplit("_", 1)
        if len(name_amount) < 2:
            await query.message.reply_text("❌ Ошибка в формате данных.")
            return

        name = name_amount[0]
        try:
            amount = float(name_amount[1])
        except ValueError:
            await query.message.reply_text("❌ Ошибка в формате суммы.")
            return

        # Проверяем, достаточно ли денег в бюджете
        budgets = get_budgets(user_id)
        total_budget = sum(budget_amount for _, budget_amount in budgets)

        if total_budget < amount:
            await query.message.edit_text(
                f"❌ Недостаточно средств в бюджете для погашения долга.\n"
                f"Требуется: {amount}₴\n"
                f"Доступно: {total_budget}₴",
                reply_markup=generate_back_button()
            )
            return

        # Закрываем долг
        if close_debt(user_id, name, -amount):  # Отрицательная сумма для долгов, которые я должен
            # Добавляем транзакцию расхода
            add_new_transaction(user_id, -amount, "Погашение долга", "расход")

            await query.message.edit_text(
                f"✅ Ваш долг {name} на сумму {amount}₴ погашен из бюджета.",
                reply_markup=generate_back_button()
            )
        else:
            await query.message.edit_text(
                f"❌ Ошибка при погашении долга {name}.",
                reply_markup=generate_back_button()
            )

    # Обработка кнопки "Долг погашен" (для долгов, которые мне должны)
    elif callback_data.startswith("debt_paid_"):
        # Извлекаем имя и сумму из callback_data
        parts = callback_data.split("_", 2)
        if len(parts) < 3:
            await query.message.reply_text("❌ Ошибка в формате данных.")
            return

        # Формат: debt_paid_name_amount
        name_amount = parts[2].rsplit("_", 1)
        if len(name_amount) < 2:
            await query.message.reply_text("❌ Ошибка в формате данных.")
            return

        name = name_amount[0]
        try:
            amount = float(name_amount[1])
        except ValueError:
            await query.message.reply_text("❌ Ошибка в формате суммы.")
            return

        # Закрываем долг
        if close_debt(user_id, name, amount):  # Положительная сумма для долгов, которые мне должны
            # Добавляем транзакцию дохода
            add_new_transaction(user_id, amount, "Возврат долга", "доход")

            await query.message.edit_text(
                f"✅ Долг {name} на сумму {amount}₴ отмечен как погашенный. Сумма добавлена в бюджет.",
                reply_markup=generate_back_button()
            )
        else:
            await query.message.edit_text(
                f"❌ Ошибка при закрытии долга {name}.",
                reply_markup=generate_back_button()
            )

    # Обработка кнопки "Подтвердить удаление долга"
    elif callback_data.startswith("confirm_delete_"):
        # Извлекаем имя и сумму из callback_data
        parts = callback_data.split("_", 3)
        if len(parts) < 4:
            await query.message.reply_text("❌ Ошибка в формате данных.")
            return

        # Формат: confirm_delete_name_amount_type
        name = parts[2]
        try:
            amount = float(parts[3].split("_")[0])
            debt_type = "_".join(parts[3].split("_")[1:])  # i_owe или owed_to_me
        except (ValueError, IndexError):
            await query.message.reply_text("❌ Ошибка в формате данных.")
            return

        # Создаем клавиатуру для подтверждения
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f"delete_debt_{name}_{amount}_{debt_type}"),
                InlineKeyboardButton("❌ Нет, отмена", callback_data=f"cancel_delete_{debt_type}")
            ]
        ]

        await query.message.edit_text(
            f"<b>⚠️ Подтверждение удаления</b>\n\nВы уверены, что хотите удалить долг <b>{name}</b> на сумму <b>{amount}₴</b>?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Обработка кнопки "Отмена удаления"
    elif callback_data.startswith("cancel_delete_"):
        debt_type = callback_data.split("_", 2)[2]  # i_owe или owed_to_me
        # Возвращаемся к списку долгов соответствующей категории
        await query.message.edit_text(
            "❌ Удаление отменено.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=f"debts_{debt_type}")]])
        )

    # Обработка кнопки "Удалить долг" (после подтверждения)
    elif callback_data.startswith("delete_debt_"):
        # Извлекаем имя и сумму из callback_data
        parts = callback_data.split("_", 3)
        if len(parts) < 4:
            await query.message.reply_text("❌ Ошибка в формате данных.")
            return

        # Формат: delete_debt_name_amount_type
        name = parts[2]
        try:
            amount = float(parts[3].split("_")[0])
            debt_type = "_".join(parts[3].split("_")[1:])  # i_owe или owed_to_me
        except (ValueError, IndexError):
            await query.message.reply_text("❌ Ошибка в формате данных.")
            return

        # Определяем знак суммы в зависимости от типа долга
        if debt_type == "i_owe":
            amount = -amount  # Я должен - отрицательная сумма

        # Закрываем долг без влияния на бюджет
        if close_debt(user_id, name, amount):
            await query.message.edit_text(
                f"✅ Долг {name} на сумму {abs(amount)}₴ удален из истории.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=f"debts_{debt_type}")]])
            )
        else:
            await query.message.edit_text(
                f"❌ Ошибка при удалении долга {name}.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=f"debts_{debt_type}")]])
            )

async def handle_message(update: Update, context: CallbackContext):
    """Обработчик сообщений для закрытия долга"""
    # Этот обработчик больше не используется для закрытия долга,
    # так как теперь используются кнопки
    pass


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
        await update.message.reply_text(f"✅ Долг сохранён: {debt_name} — {amount}₴")
    else:
        await update.message.reply_text("❌ Произошла ошибка при сохранении долга.")

    return ConversationHandler.END


async def cancel_add_debt(update: Update, context: CallbackContext):
    """Отменяет добавление долга"""
    await update.message.reply_text("🚫 Добавление долга отменено.")
    return ConversationHandler.END


async def handle_debt_amount_input(update: Update, context: CallbackContext):
    """Обрабатывает ввод суммы долга"""
    try:
        amount = float(update.message.text)
        context.user_data["debt_amount"] = amount

        await update.message.reply_text(
            "Название долга (ФИО или организация):"
        )
        return DEBT_NAME_INPUT
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите корректное число.")
        return DEBT_AMOUNT_INPUT


async def handle_debt_name_input(update: Update, context: CallbackContext):
    """Обрабатывает ввод названия долга и сохраняет долг"""
    user_id = update.effective_user.id

    # Проверяем, что update.message не None
    if update.message is None:
        print("Error: update.message is None in handle_debt_name_input")
        return ConversationHandler.END

    debt_name = update.message.text
    debt_amount = context.user_data.get("debt_amount", 0)
    debt_type = context.user_data.get("debt_type", "owed_to_me")

    # Проверяем, что debt_name не пустой
    if not debt_name or debt_name.strip() == "":
        await update.message.reply_text("❌ Название долга не может быть пустым. Попробуйте снова.")
        return DEBT_NAME_INPUT

    # Если тип долга "я должен", меняем знак суммы на отрицательный
    if debt_type == "i_owe":
        debt_amount = -abs(debt_amount)
    else:
        debt_amount = abs(debt_amount)

    # Логируем данные перед сохранением
    print(f"Saving debt: user_id={user_id}, debt_name='{debt_name}', debt_amount={debt_amount}, debt_type={debt_type}")

    # Сохраняем долг и проверяем результат
    save_result = save_debt(user_id, debt_name, debt_amount)

    print(f"Save result: {save_result}")

    if save_result:
        if debt_type == "i_owe":
            await update.message.reply_text(
                f"✅ Долг сохранён: Вы должны {debt_name} — {abs(debt_amount)}₴",
                reply_markup=generate_debt_confirmation_keyboard()
            )
        else:
            await update.message.reply_text(
                f"✅ Долг сохранён: {debt_name} должен вам — {debt_amount}₴",
                reply_markup=generate_debt_confirmation_keyboard()
            )
    else:
        await update.message.reply_text("❌ Произошла ошибка при сохранении долга.")

    return ConversationHandler.END


async def send_debt_reminder(context: CallbackContext):
    """Отправляет напоминание о долгах"""
    job = context.job
    user_id = job.chat_id
    debts = get_active_debts(user_id)
    if debts:
        text = "🔔 Напоминание о долгах:\n\n"

        # Долги, которые пользователь должен другим
        debts_i_owe = [(name, amount) for name, amount in debts if amount < 0]
        if debts_i_owe:
            text += "💸 Вы должны:\n"
            for name, amount in debts_i_owe:
                text += f"• {name}: {abs(amount)}₴\n"
            text += "\n"

        # Долги, которые должны пользователю
        debts_owed_to_me = [(name, amount) for name, amount in debts if amount > 0]
        if debts_owed_to_me:
            text += "💰 Вам должны:\n"
            for name, amount in debts_owed_to_me:
                text += f"• {name}: {amount}₴\n"

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
            await update.message.reply_text(
                f"✅ Долг добавлен: {name} — {amount}₴",
                reply_markup=generate_debt_confirmation_keyboard()
            )
        else:
            await update.message.reply_text("❌ Произошла ошибка при сохранении долга.")

    except (ValueError, IndexError):
        await update.message.reply_text("❌ Формат: `/adddebt имя сумма`\nПример: `/adddebt Алексей 3000`", parse_mode="Markdown")


def generate_back_button():
    """Генерирует кнопку 'Назад'"""
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="debt_back")]]
    return InlineKeyboardMarkup(keyboard)


def generate_debt_confirmation_keyboard():
    """Генерирует клавиатуру для сообщения о сохранении долга"""
    keyboard = [
        [InlineKeyboardButton("🔙 Вернуться к долгам", callback_data="debt_back")],
        [InlineKeyboardButton("➕ Новый долг", callback_data="add_debt")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Регистрация обработчиков
debt_handler = CallbackQueryHandler(handle_debt_callback, pattern='^debt$')
debt_command_handler = CommandHandler("debt", handle_debt_callback)
debt_menu_handler = CallbackQueryHandler(debt_menu_button_handler, pattern='^(view_debts|debt_history|close_debt|add_debt|remind_debt|help_debt|debt_back)$')
debt_category_handler = CallbackQueryHandler(show_debts_by_category, pattern='^(debts_i_owe|debts_owed_to_me)$')
debt_action_handler = CallbackQueryHandler(handle_debt_action, pattern='^(pay_debt_|debt_paid_|delete_debt_|confirm_delete_|cancel_delete_)')
debt_message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
adddebt_handler = CommandHandler("adddebt", adddebt_command)
set_reminder_handler = CommandHandler("debtreminder", set_daily_reminder)

# Обработчик диалога добавления долга
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
