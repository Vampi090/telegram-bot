from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, filters, MessageHandler, \
    ConversationHandler
from keyboards.budget_menu import budget_menu_keyboard
from services.logging_service import log_command_usage
from services.database_service import (
    add_goal, get_goals, set_budget, get_budgets,
    add_piggy_bank_goal, get_piggy_bank_goals, add_funds_to_goal,
    delete_piggy_bank_goal, get_piggy_bank_goal
)
from utils.menu_utils import send_or_edit_menu


async def handle_budgeting_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)
    user = update.effective_user

    reply_markup = budget_menu_keyboard()

    await send_or_edit_menu(update, context, "📥 Меню бюджету", reply_markup)


async def handle_goal_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = None
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        await update.callback_query.answer()

    if not user_id:
        return

    if context.args and len(context.args) >= 2:
        try:
            amount = float(context.args[0])
            description = " ".join(context.args[1:])

            success = add_goal(user_id, amount, description)

            if success:
                text = f"🎯 Ціль '{description}' на суму {amount} грн встановлена!"
            else:
                text = "❌ Сталася помилка при додаванні цілі."
        except ValueError:
            text = "❌ Невірний формат! Використовуйте: /goal [сума] [опис]"

        back_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="budgeting")]
        ])

        await send_or_edit_menu(update, context, text, back_button)
        return

    goals = get_goals(user_id)

    if not goals:
        text = "🎯 У вас поки немає фінансових цілей."
    else:
        text = "🎯 *Ваші фінансові цілі:*\n"
        for amount, description, date in goals:
            text += f"🔹 {description}: {amount} грн (дата: {date})\n"

    back_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад", callback_data="budgeting")]
    ])

    await send_or_edit_menu(update, context, text, back_button, parse_mode="Markdown")


async def handle_budget_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id

    if update.callback_query:
        await update.callback_query.answer()

    if context.user_data.get('budget_message_id'):
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id,
                                             message_id=context.user_data['budget_message_id'])
        except Exception:
            pass

    args = context.args if update.message else []

    back_button_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад", callback_data="budgeting")]
    ])

    if len(args) == 2:
        category = " ".join(args[:-1])
        try:
            amount = float(args[-1])
        except ValueError:
            msg = await context.bot.send_message(
                chat_id=user_id,
                text="❌ Помилка! Введіть коректне число для суми бюджету.",
                reply_markup=back_button_markup
            )
            context.user_data['budget_message_id'] = msg.message_id
            return

        success = set_budget(user_id, category, amount)

        if success:
            msg = await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Бюджет для категорії '*{category}*' встановлено: *{amount} грн*",
                parse_mode="Markdown",
                reply_markup=back_button_markup
            )
        else:
            msg = await context.bot.send_message(
                chat_id=user_id,
                text="❌ Сталася помилка при встановленні бюджету.",
                reply_markup=back_button_markup
            )
        context.user_data['budget_message_id'] = msg.message_id

    else:
        budgets = get_budgets(user_id)

        if not budgets:
            msg = await context.bot.send_message(
                chat_id=user_id,
                text="💡 У вас поки немає встановленого бюджету.",
                reply_markup=back_button_markup
            )
            context.user_data['budget_message_id'] = msg.message_id
            return

        total_budget = sum(amount for _, amount in budgets)

        message_lines = ["📊 *Ваші бюджети:*"]
        message_lines.append("\n💼 *Загальний бюджет:*")
        message_lines.append(f"💰 `{total_budget} грн`")
        message_lines.append("\n📋 *Бюджет за категоріями:*")
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
    if context.user_data.get('budget_message_id'):
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id,
                                             message_id=context.user_data['budget_message_id'])
        except Exception:
            pass

        context.user_data['budget_message_id'] = None


async def track_goals(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

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
        await context.bot.send_message(chat_id=user_id, text="🎯 У вас поки немає встановлених цілей.")
        return

    message_lines = ["📌 *Ваші фінансові цілі:*"]
    for amount, description, date in goals:
        message_lines.append(f"💰 {description}: {amount} грн (встановлено {date})")

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


async def handle_piggy_bank_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    context.user_data.pop('piggy_bank_name', None)
    context.user_data.pop('piggy_bank_amount', None)
    context.user_data.pop('piggy_bank_state', None)

    user_id = None
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        await update.callback_query.answer()

    if not user_id:
        return

    goals = get_piggy_bank_goals(user_id)

    keyboard = []

    keyboard.append([InlineKeyboardButton("➕ Створити нову ціль", callback_data='piggy_bank_create')])

    if goals:
        for goal_id, name, target_amount, current_amount, _, _, completed in goals:
            progress = int((current_amount / target_amount) * 100) if target_amount > 0 else 0
            status = "✅" if completed else f"{progress}%"

            button_text = f"{name} - {status}"

            keyboard.append([InlineKeyboardButton(button_text, callback_data=f'piggy_bank_view_{goal_id}')])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='budgeting')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if goals:
        text = "🐷 *Ваша скарбничка*\n\nОберіть ціль для перегляду деталей або створіть нову:"
    else:
        text = "🐷 *Ваша скарбничка порожня*\n\nСтворіть нову ціль, щоб почати накопичувати:"

    await send_or_edit_menu(update, context, text, reply_markup, parse_mode="Markdown")


async def handle_piggy_bank_create(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    context.user_data.pop('piggy_bank_name', None)
    context.user_data.pop('piggy_bank_amount', None)
    context.user_data.pop('piggy_bank_state', None)

    context.user_data['piggy_bank_state'] = 'waiting_for_name'

    keyboard = [[InlineKeyboardButton("🔙 Скасувати", callback_data='piggy_bank')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_or_edit_menu(update, context, "Введіть назву цілі:", reply_markup)

    return 'waiting_for_name'


async def handle_piggy_bank_name_input(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.message.from_user.id
    name = update.message.text

    context.user_data['piggy_bank_name'] = name

    context.user_data['piggy_bank_state'] = 'waiting_for_amount'

    keyboard = [[InlineKeyboardButton("🔙 Скасувати", callback_data='piggy_bank')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text=f"Ціль: *{name}*\n\nВведіть суму, яку хочете накопичити:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    return 'waiting_for_amount'


async def handle_piggy_bank_amount_input(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.message.from_user.id
    amount_text = update.message.text

    try:
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError("Amount must be positive")

        name = context.user_data.get('piggy_bank_name', '')

        context.user_data['piggy_bank_state'] = 'waiting_for_description'
        context.user_data['piggy_bank_amount'] = amount

        keyboard = [
            [InlineKeyboardButton("⏩ Пропустити", callback_data='piggy_bank_skip_description')],
            [InlineKeyboardButton("🔙 Скасувати", callback_data='piggy_bank')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text=f"Ціль: *{name}*\nСума: *{amount} грн*\n\nВведіть опис цілі (або натисніть 'Пропустити'):",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

        return 'waiting_for_description'
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Скасувати", callback_data='piggy_bank')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text="❌ Будь ласка, введіть коректну суму (додатнє число):",
            reply_markup=reply_markup
        )

        return 'waiting_for_amount'


async def handle_piggy_bank_description_input(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.message.from_user.id
    description = update.message.text

    name = context.user_data.get('piggy_bank_name', '')
    amount = context.user_data.get('piggy_bank_amount', 0)

    success = add_piggy_bank_goal(user_id, name, amount, description)

    context.user_data.pop('piggy_bank_name', None)
    context.user_data.pop('piggy_bank_amount', None)
    context.user_data.pop('piggy_bank_state', None)

    keyboard = [[InlineKeyboardButton("🔙 Назад до скарбнички", callback_data='piggy_bank')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if success:
        await update.message.reply_text(
            text=f"✅ Ціль *{name}* на суму *{amount} грн* успішно створена!",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text="❌ Сталася помилка при створенні цілі. Будь ласка, спробуйте ще раз.",
            reply_markup=reply_markup
        )

    return ConversationHandler.END


async def handle_piggy_bank_skip_description(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    name = context.user_data.get('piggy_bank_name', '')
    amount = context.user_data.get('piggy_bank_amount', 0)

    success = add_piggy_bank_goal(user_id, name, amount, "")

    context.user_data.pop('piggy_bank_name', None)
    context.user_data.pop('piggy_bank_amount', None)
    context.user_data.pop('piggy_bank_state', None)

    if success:
        text = f"✅ Ціль *{name}* на суму *{amount} грн* успішно створена!"
    else:
        text = "❌ Сталася помилка при створенні цілі. Будь ласка, спробуйте ще раз."

    await handle_piggy_bank_callback(update, context)

    return ConversationHandler.END


async def handle_piggy_bank_view(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    callback_data = update.callback_query.data
    goal_id = int(callback_data.split('_')[-1])

    goal = get_piggy_bank_goal(user_id, goal_id)

    if not goal:
        await handle_piggy_bank_callback(update, context)
        return

    goal_id, name, target_amount, current_amount, description, created_date, completed = goal

    progress = int((current_amount / target_amount) * 100) if target_amount > 0 else 0

    text = f"🐷 *{name}*\n\n"
    text += f"💰 Ціль: *{target_amount} грн*\n"
    text += f"💵 Накопичено: *{current_amount} грн*\n"
    text += f"📊 Прогрес: *{progress}%*\n"

    if description:
        text += f"\n📝 Опис: _{description}_\n"

    text += f"\n📅 Створено: {created_date}"

    keyboard = []

    if not completed:
        keyboard.append([InlineKeyboardButton("💰 Додати кошти", callback_data=f'piggy_bank_add_funds_{goal_id}')])

    keyboard.append([InlineKeyboardButton("❌ Видалити ціль", callback_data=f'piggy_bank_delete_{goal_id}')])
    keyboard.append([InlineKeyboardButton("🔙 Назад до скарбнички", callback_data='piggy_bank')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_or_edit_menu(update, context, text, reply_markup, parse_mode="Markdown")


async def handle_piggy_bank_add_funds(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    callback_data = update.callback_query.data
    goal_id = int(callback_data.split('_')[-1])

    goal = get_piggy_bank_goal(user_id, goal_id)

    if not goal or goal[6]:
        await handle_piggy_bank_callback(update, context)
        return

    context.user_data.pop('piggy_bank_name', None)
    context.user_data.pop('piggy_bank_amount', None)
    context.user_data.pop('piggy_bank_state', None)
    context.user_data.pop('piggy_bank_goal_id', None)

    context.user_data['piggy_bank_goal_id'] = goal_id
    context.user_data['piggy_bank_state'] = 'waiting_for_funds'

    keyboard = [[InlineKeyboardButton("🔙 Скасувати", callback_data=f'piggy_bank_view_{goal_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    goal_id, name, target_amount, current_amount, _, _, _ = goal

    budgets = get_budgets(user_id)
    total_budget = sum(amount for _, amount in budgets)

    text = (f"🐷 *{name}*\n\n"
            f"💰 Ціль: *{target_amount} грн*\n"
            f"💵 Накопичено: *{current_amount} грн*\n"
            f"💸 Залишилось: *{target_amount - current_amount} грн*\n\n"
            f"💼 Доступно в бюджеті: *{total_budget} грн*\n\n"
            f"Введіть суму, яку хочете додати:")

    await send_or_edit_menu(update, context, text, reply_markup, parse_mode="Markdown")

    return 'waiting_for_funds'


async def handle_piggy_bank_funds_input(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.message.from_user.id
    amount_text = update.message.text

    try:
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError("Amount must be positive")

        goal_id = context.user_data.get('piggy_bank_goal_id')

        if not goal_id:
            keyboard = [[InlineKeyboardButton("🔙 Назад до скарбнички", callback_data='piggy_bank')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                text="❌ Сталася помилка. Будь ласка, спробуйте ще раз.",
                reply_markup=reply_markup
            )
            return ConversationHandler.END

        goal = get_piggy_bank_goal(user_id, goal_id)

        if not goal:
            keyboard = [[InlineKeyboardButton("🔙 Назад до скарбнички", callback_data='piggy_bank')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                text="❌ Ціль не знайдена. Будь ласка, спробуйте ще раз.",
                reply_markup=reply_markup
            )
            return ConversationHandler.END

        goal_id, name, target_amount, current_amount, _, _, completed = goal

        budgets = get_budgets(user_id)
        total_budget = sum(amount for _, amount in budgets)

        if total_budget < amount:
            keyboard = [[InlineKeyboardButton("🔙 Назад до цілі", callback_data=f'piggy_bank_view_{goal_id}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                text=f"❌ Недостатньо коштів у бюджеті. Доступно: *{total_budget} грн*",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return ConversationHandler.END

        success = add_funds_to_goal(user_id, goal_id, amount)

        context.user_data.pop('piggy_bank_goal_id', None)
        context.user_data.pop('piggy_bank_state', None)

        keyboard = [[InlineKeyboardButton("🔙 Назад до цілі", callback_data=f'piggy_bank_view_{goal_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if success:
            updated_goal = get_piggy_bank_goal(user_id, goal_id)
            _, _, _, new_current_amount, _, _, new_completed = updated_goal

            if new_completed and not completed:
                await update.message.reply_text(
                    text=f"🎉 Вітаємо! Ви досягли цілі *{name}*!\n\n"
                         f"💰 Накопичено: *{new_current_amount} грн*\n"
                         f"💸 Кошти списані з бюджету.",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    text=f"✅ *{amount} грн* успішно додано до цілі *{name}*!\n\n"
                         f"💰 Поточний прогрес: *{new_current_amount} / {target_amount} грн*\n"
                         f"💸 Кошти списані з бюджету.",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text(
                text="❌ Сталася помилка при додаванні коштів. Будь ласка, спробуйте ще раз.",
                reply_markup=reply_markup
            )

        return ConversationHandler.END
    except ValueError:
        goal_id = context.user_data.get('piggy_bank_goal_id')
        keyboard = [[InlineKeyboardButton("🔙 Скасувати", callback_data=f'piggy_bank_view_{goal_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text="❌ Будь ласка, введіть коректну суму (додатнє число):",
            reply_markup=reply_markup
        )

        return 'waiting_for_funds'


async def handle_piggy_bank_delete(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    callback_data = update.callback_query.data
    goal_id = int(callback_data.split('_')[-1])

    goal = get_piggy_bank_goal(user_id, goal_id)

    if not goal:
        await handle_piggy_bank_callback(update, context)
        return

    goal_id, name, _, _, _, _, _ = goal

    keyboard = [
        [InlineKeyboardButton("✅ Так, видалити", callback_data=f'piggy_bank_delete_confirm_{goal_id}')],
        [InlineKeyboardButton("❌ Ні, скасувати", callback_data=f'piggy_bank_view_{goal_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_or_edit_menu(
        update,
        context,
        f"❓ Ви впевнені, що хочете видалити ціль *{name}*?",
        reply_markup,
        parse_mode="Markdown"
    )


async def handle_piggy_bank_delete_confirm(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    callback_data = update.callback_query.data
    goal_id = int(callback_data.split('_')[-1])

    goal = get_piggy_bank_goal(user_id, goal_id)

    if not goal:
        await handle_piggy_bank_callback(update, context)
        return

    goal_id, name, _, _, _, _, _ = goal

    success = delete_piggy_bank_goal(user_id, goal_id)

    if success:
        await send_or_edit_menu(
            update,
            context,
            f"✅ Ціль *{name}* успішно видалена!",
            None,
            parse_mode="Markdown"
        )
        import asyncio
        await asyncio.sleep(1)
        await handle_piggy_bank_callback(update, context)
    else:
        keyboard = [[InlineKeyboardButton("🔙 Назад до цілі", callback_data=f'piggy_bank_view_{goal_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await send_or_edit_menu(
            update,
            context,
            "❌ Сталася помилка при видаленні цілі. Будь ласка, спробуйте ще раз.",
            reply_markup
        )


piggy_bank_create_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_piggy_bank_create, pattern='^piggy_bank_create$')],
    states={
        'waiting_for_name': [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_piggy_bank_name_input)],
        'waiting_for_amount': [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_piggy_bank_amount_input)],
        'waiting_for_description': [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_piggy_bank_description_input),
            CallbackQueryHandler(handle_piggy_bank_skip_description, pattern='^piggy_bank_skip_description$')
        ],
    },
    fallbacks=[
        CallbackQueryHandler(handle_piggy_bank_callback, pattern='^piggy_bank$'),
        CallbackQueryHandler(handle_piggy_bank_create, pattern='^piggy_bank_create$'),
        MessageHandler(filters.COMMAND, handle_piggy_bank_callback)
    ],
    name="piggy_bank_create",
    persistent=False
)

piggy_bank_add_funds_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_piggy_bank_add_funds, pattern='^piggy_bank_add_funds_[0-9]+$')],
    states={
        'waiting_for_funds': [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_piggy_bank_funds_input)],
    },
    fallbacks=[
        CallbackQueryHandler(handle_piggy_bank_view, pattern='^piggy_bank_view_'),
        CallbackQueryHandler(handle_piggy_bank_callback, pattern='^piggy_bank$'),
        MessageHandler(filters.COMMAND, handle_piggy_bank_callback)
    ],
    name="piggy_bank_add_funds",
    persistent=False
)

budgeting_handler = CallbackQueryHandler(handle_budgeting_callback, pattern='^budgeting$')
goal_handler = CallbackQueryHandler(handle_goal_callback, pattern='^goal$')
budget_handler = CallbackQueryHandler(handle_budget_callback, pattern='^budget$')
goal_command_handler = CommandHandler('goal', handle_goal_callback)
budget_command_handler = CommandHandler('budget', handle_budget_callback)
track_goals_handler = CommandHandler('track_goals', track_goals)

piggy_bank_handler = CallbackQueryHandler(handle_piggy_bank_callback, pattern='^piggy_bank$')
piggy_bank_view_handler = CallbackQueryHandler(handle_piggy_bank_view, pattern='^piggy_bank_view_')
piggy_bank_delete_handler = CallbackQueryHandler(handle_piggy_bank_delete, pattern='^piggy_bank_delete_[0-9]+$')
piggy_bank_delete_confirm_handler = CallbackQueryHandler(handle_piggy_bank_delete_confirm,
                                                         pattern='^piggy_bank_delete_confirm_')
