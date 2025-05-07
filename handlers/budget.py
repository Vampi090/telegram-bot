from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, filters, MessageHandler, ConversationHandler
from keyboards.budget_menu import budget_menu_keyboard
from services.logging_service import log_command_usage
from services.database_service import add_goal, get_goals, set_budget, get_budgets


async def handle_budgeting_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)
    user = update.effective_user

    reply_markup = budget_menu_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="📥 Меню бюджету",
            reply_markup=reply_markup
        )


async def handle_goal_callback(update: Update, context: CallbackContext):
    """Обработчик для установки и просмотра целей."""
    await log_command_usage(update, context)

    user_id = None
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        await update.callback_query.answer()

    if not user_id:
        return

    # Добавление цели
    if context.args and len(context.args) >= 2:
        try:
            amount = float(context.args[0])
            description = " ".join(context.args[1:])

            success = add_goal(user_id, amount, description)

            if success:
                text = f"🎯 Цель '{description}' на сумму {amount} грн установлена!"
            else:
                text = "❌ Произошла ошибка при добавлении цели."
        except ValueError:
            text = "❌ Неверный формат! Используйте: /goal [сумма] [описание]"

        back_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="budgeting")]
        ])

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=back_button
            )
        else:
            await update.message.reply_text(text, reply_markup=back_button)
        return

    # Показ целей
    goals = get_goals(user_id)

    if not goals:
        text = "🎯 У вас пока нет финансовых целей."
    else:
        text = "🎯 *Ваши финансовые цели:*\n"
        for amount, description, date in goals:
            text += f"🔹 {description}: {amount} грн (дата: {date})\n"

    back_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад", callback_data="budgeting")]
    ])

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=back_button
        )
    else:
        await update.message.reply_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=back_button
        )


async def handle_budget_callback(update: Update, context: CallbackContext):
    """Обработчик для установки и просмотра бюджета."""
    await log_command_usage(update, context)

    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id

    # Закрываем "часики", если это callback_query
    if update.callback_query:
        await update.callback_query.answer()

    # Сбрасываем предыдущее сообщение (если оно существует)
    if context.user_data.get('budget_message_id'):
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id,
                                            message_id=context.user_data['budget_message_id'])
        except Exception:
            pass  # Игнорируем, если сообщение уже удалено

    args = context.args if update.message else []

    # Создаём InlineKeyboardMarkup с кнопкой Назад
    back_button_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад", callback_data="budgeting")]
    ])

    if len(args) == 2:
        # Установка бюджета
        category = " ".join(args[:-1])  # Поддержка категорий из нескольких слов
        try:
            amount = float(args[-1])
        except ValueError:
            msg = await context.bot.send_message(
                chat_id=user_id,
                text="❌ Ошибка! Введите корректное число для суммы бюджета.",
                reply_markup=back_button_markup
            )
            context.user_data['budget_message_id'] = msg.message_id
            return

        success = set_budget(user_id, category, amount)

        if success:
            msg = await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Бюджет для категории '*{category}*' установлен: *{amount} грн*",
                parse_mode="Markdown",
                reply_markup=back_button_markup
            )
        else:
            msg = await context.bot.send_message(
                chat_id=user_id,
                text="❌ Произошла ошибка при установке бюджета.",
                reply_markup=back_button_markup
            )
        context.user_data['budget_message_id'] = msg.message_id

    else:
        # Просмотр бюджета
        budgets = get_budgets(user_id)

        if not budgets:
            msg = await context.bot.send_message(
                chat_id=user_id,
                text="💡 У вас пока нет установленного бюджета.",
                reply_markup=back_button_markup
            )
            context.user_data['budget_message_id'] = msg.message_id
            return

        # Calculate total budget
        total_budget = sum(amount for _, amount in budgets)

        message_lines = ["📊 *Ваши бюджеты:*"]

        # Add total budget section
        message_lines.append("\n💼 *Общий бюджет:*")
        message_lines.append(f"💰 `{total_budget} грн`")

        # Add category budget section
        message_lines.append("\n📋 *Бюджет по категориям:*")
        for category, amount in budgets:
            message_lines.append(f"💰 *{category}*: `{amount} грн`")

        msg = await context.bot.send_message(
            chat_id=user_id,
            text="\n".join(message_lines),
            parse_mode="Markdown",
            reply_markup=back_button_markup
        )
        context.user_data['budget_message_id'] = msg.message_id


async def close_budget_if_active(update: Update, context: CallbackContext):
    """Закрывает активное сообщение бюджета, если оно существует."""
    # Проверяем, если активное сообщение бюджета существует
    if context.user_data.get('budget_message_id'):
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id,
                                            message_id=context.user_data['budget_message_id'])
        except Exception:
            pass  # Игнорируем ошибки, если сообщение уже удалено

        # Сбрасываем состояние
        context.user_data['budget_message_id'] = None


async def track_goals(update: Update, context: CallbackContext):
    """Отслеживает прогресс по целям."""
    await log_command_usage(update, context)

    # Определяем user_id и query
    user_id = None
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        await update.callback_query.answer()

    if not user_id:
        return

    goals = get_goals(user_id)

    if not goals:
        await context.bot.send_message(chat_id=user_id, text="🎯 У вас пока нет установленных целей.")
        return

    message_lines = ["📌 *Ваши финансовые цели:*"]
    for amount, description, date in goals:
        message_lines.append(f"💰 {description}: {amount} грн (установлено {date})")

    back_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад", callback_data="budgeting")]
    ])

    message = "\n".join(message_lines)
    await context.bot.send_message(
        chat_id=user_id, 
        text=message, 
        parse_mode="Markdown",
        reply_markup=back_button
    )


# Регистрация обработчиков
budgeting_handler = CallbackQueryHandler(handle_budgeting_callback, pattern='^budgeting$')
goal_handler = CallbackQueryHandler(handle_goal_callback, pattern='^goal$')
budget_handler = CallbackQueryHandler(handle_budget_callback, pattern='^budget$')
goal_command_handler = CommandHandler('goal', handle_goal_callback)
budget_command_handler = CommandHandler('budget', handle_budget_callback)
track_goals_handler = CommandHandler('track_goals', track_goals)
