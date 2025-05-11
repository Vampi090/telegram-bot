from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, filters, MessageHandler, \
    ConversationHandler
from datetime import datetime, timedelta
import calendar
from keyboards.reminder_menu import reminder_menu_keyboard
from services.logging_service import log_command_usage
from services.database_service import (
    add_reminder, get_reminders, get_reminder,
    update_reminder, delete_reminder, mark_reminder_completed
)
from .budget import handle_budgeting_callback

TITLE, DATETIME, EDIT_TITLE, EDIT_DATETIME, SELECT_DATE, SELECT_TIME = range(6)


async def handle_reminder_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    context.user_data.pop('reminder_title', None)
    context.user_data.pop('reminder_id', None)

    user_id = None
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        await update.callback_query.answer()

    if not user_id:
        return

    reply_markup = reminder_menu_keyboard()

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text="⏰ Меню нагадувань",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text="⏰ Меню нагадувань",
            reply_markup=reply_markup
        )


async def handle_create_reminder(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    context.user_data.pop('reminder_title', None)

    keyboard = [[InlineKeyboardButton("🔙 Скасувати", callback_data='reminder')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text="Введіть текст нагадування:",
        reply_markup=reply_markup
    )

    return TITLE


async def handle_reminder_title_input(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.message.from_user.id
    title = update.message.text

    context.user_data['reminder_title'] = title

    now = datetime.now()
    context.user_data['reminder_year'] = now.year
    context.user_data['reminder_month'] = now.month
    context.user_data['reminder_day'] = now.day
    context.user_data['reminder_hour'] = now.hour
    context.user_data['reminder_minute'] = 0

    keyboard = generate_date_selection_keyboard(context)

    keyboard.append([InlineKeyboardButton("🔙 Скасувати", callback_data='reminder')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text=f"Нагадування: *{title}*\n\nОберіть дату нагадування:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    return SELECT_DATE


def generate_date_selection_keyboard(context):
    year = context.user_data.get('reminder_year', datetime.now().year)
    month = context.user_data.get('reminder_month', datetime.now().month)

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

                is_selected = day == context.user_data.get('reminder_day', 0)

                button_text = str(day)
                if is_selected:
                    button_text = f"✓{day}"

                callback_data = f"date_{year}_{month}_{day}" if not is_past else "ignore"

                week_buttons.append(InlineKeyboardButton(button_text, callback_data=callback_data))

                day += 1

        if any(button.text.strip() != "" for button in week_buttons):
            keyboard.append(week_buttons)

    keyboard.append([InlineKeyboardButton("⏰ Обрати час", callback_data="select_time")])

    return keyboard


async def handle_date_selection(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    query = update.callback_query
    await query.answer()

    callback_data = query.data
    if callback_data.startswith("date_prev_") or callback_data.startswith("date_next_"):
        parts = callback_data.split("_")
        year = int(parts[2])
        month = int(parts[3])

        context.user_data['reminder_year'] = year
        context.user_data['reminder_month'] = month

        keyboard = generate_date_selection_keyboard(context)
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_reply_markup(reply_markup=reply_markup)
        return SELECT_DATE

    elif callback_data.startswith("date_"):
        parts = callback_data.split("_")
        year = int(parts[1])
        month = int(parts[2])
        day = int(parts[3])

        context.user_data['reminder_year'] = year
        context.user_data['reminder_month'] = month
        context.user_data['reminder_day'] = day

        keyboard = generate_date_selection_keyboard(context)
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_reply_markup(reply_markup=reply_markup)
        return SELECT_DATE

    elif callback_data == "select_time":
        keyboard = generate_time_selection_keyboard(context)
        reply_markup = InlineKeyboardMarkup(keyboard)

        title = context.user_data.get('reminder_title', '')
        year = context.user_data.get('reminder_year')
        month = context.user_data.get('reminder_month')
        day = context.user_data.get('reminder_day')

        date_str = f"{day:02d}.{month:02d}.{year}"

        await query.edit_message_text(
            text=f"Нагадування: *{title}*\n\nДата: *{date_str}*\n\nОберіть час нагадування:\n(спочатку оберіть годину, потім хвилини)",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return SELECT_TIME

    return SELECT_DATE


def generate_time_selection_keyboard(context):
    hour = context.user_data.get('reminder_hour', 12)
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

        title = context.user_data.get('reminder_title', '')

        await query.edit_message_text(
            text=f"Нагадування: *{title}*\n\nОберіть дату нагадування:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return SELECT_DATE

    elif callback_data == "save_reminder":
        user_id = query.from_user.id
        year = context.user_data.get('reminder_year')
        month = context.user_data.get('reminder_month')
        day = context.user_data.get('reminder_day')
        hour = context.user_data.get('reminder_hour')
        minute = context.user_data.get('reminder_minute')

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

            reminder_id = context.user_data.get('reminder_id')

            if reminder_id:
                success = update_reminder(user_id, reminder_id, reminder_datetime=reminder_datetime_str)
                keyboard = [
                    [InlineKeyboardButton("🔙 Назад до нагадування", callback_data=f'view_reminder_{reminder_id}')]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                if success:
                    await query.edit_message_text(
                        text=f"✅ Дата та час нагадування успішно змінені на: *{reminder_datetime.strftime('%d.%m.%Y %H:%M')}*",
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
                else:
                    await query.edit_message_text(
                        text="❌ Сталася помилка під час зміни дати та часу нагадування. Будь ласка, спробуйте ще раз.",
                        reply_markup=reply_markup
                    )
            else:
                title = context.user_data.get('reminder_title', '')
                reminder_id = add_reminder(user_id, title, reminder_datetime_str)

                keyboard = [[InlineKeyboardButton("🔙 Назад до нагадувань", callback_data='reminder')]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                if reminder_id:
                    await query.edit_message_text(
                        text=f"✅ Нагадування успішно створено!\n\n"
                             f"📝 *{title}*\n"
                             f"⏰ {reminder_datetime.strftime('%d.%m.%Y %H:%M')}",
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
                else:
                    await query.edit_message_text(
                        text="❌ Сталася помилка під час створення нагадування. Будь ласка, спробуйте ще раз.",
                        reply_markup=reply_markup
                    )

            context.user_data.pop('reminder_title', None)
            context.user_data.pop('reminder_year', None)
            context.user_data.pop('reminder_month', None)
            context.user_data.pop('reminder_day', None)
            context.user_data.pop('reminder_hour', None)
            context.user_data.pop('reminder_minute', None)
            context.user_data.pop('reminder_id', None)

            return ConversationHandler.END
        except ValueError:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_date")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                text="❌ Некоректна дата або час. Будь ласка, оберіть іншу дату або час.",
                reply_markup=reply_markup
            )
            return SELECT_TIME

    return SELECT_TIME


async def handle_reminder_datetime_input(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.message.from_user.id
    datetime_text = update.message.text

    try:
        reminder_datetime = datetime.strptime(datetime_text, "%Y-%m-%d %H:%M")
        reminder_datetime_str = reminder_datetime.strftime("%Y-%m-%d %H:%M:%S")

        title = context.user_data.get('reminder_title', '')

        reminder_id = add_reminder(user_id, title, reminder_datetime_str)

        keyboard = [[InlineKeyboardButton("🔙 Назад до нагадувань", callback_data='reminder')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if reminder_id:
            await update.message.reply_text(
                text=f"✅ Нагадування успішно створено!\n\n"
                     f"📝 *{title}*\n"
                     f"⏰ {reminder_datetime.strftime('%d.%m.%Y %H:%M')}",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text="❌ Сталася помилка під час створення нагадування. Будь ласка, спробуйте ще раз.",
                reply_markup=reply_markup
            )

        context.user_data.pop('reminder_title', None)

        return ConversationHandler.END
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Скасувати", callback_data='reminder')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text="❌ Некоректний формат дати та часу. Будь ласка, введіть у форматі РРРР-ММ-ДД ГГ:ХХ\nНаприклад: 2023-12-31 23:59",
            reply_markup=reply_markup
        )

        return DATETIME


async def handle_list_reminders(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    reminders = get_reminders(user_id)

    # Check if we're coming from the debt menu
    from_debt_menu = context.user_data.get('return_to_debt_menu', False)
    back_callback = 'remind_debt' if from_debt_menu else 'reminder'

    if not reminders:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=back_callback)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text="📋 У вас поки що немає нагадувань.",
            reply_markup=reply_markup
        )
        return

    keyboard = []

    for reminder_id, title, reminder_datetime, _, _ in reminders:
        dt = datetime.strptime(reminder_datetime, "%Y-%m-%d %H:%M:%S")
        formatted_datetime = dt.strftime("%d.%m.%Y %H:%M")

        button_text = f"{title} - {formatted_datetime}"

        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'view_reminder_{reminder_id}')])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=back_callback)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text="📋 Ваші нагадування:",
        reply_markup=reply_markup
    )


async def handle_view_reminder(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    callback_data = update.callback_query.data
    reminder_id = int(callback_data.split('_')[-1])

    reminder = get_reminder(user_id, reminder_id)

    if not reminder:
        await handle_list_reminders(update, context)
        return

    reminder_id, title, reminder_datetime, created_at, is_completed = reminder

    dt = datetime.strptime(reminder_datetime, "%Y-%m-%d %H:%M:%S")
    created = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")

    formatted_datetime = dt.strftime("%d.%m.%Y %H:%M")
    formatted_created = created.strftime("%d.%m.%Y %H:%M")

    text = f"📝 *{title}*\n\n"
    text += f"⏰ Дата та час: *{formatted_datetime}*\n"
    text += f"📅 Створено: {formatted_created}\n"

    status = "✅ Виконано" if is_completed else "⏳ Активно"
    text += f"📊 Статус: *{status}*"

    keyboard = []

    if not is_completed:
        keyboard.append([InlineKeyboardButton("✏️ Змінити", callback_data=f'edit_reminder_{reminder_id}')])
        keyboard.append(
            [InlineKeyboardButton("✅ Відмітити як виконане", callback_data=f'complete_reminder_{reminder_id}')])

    keyboard.append([InlineKeyboardButton("❌ Видалити", callback_data=f'delete_reminder_{reminder_id}')])

    # Check if we're coming from the debt menu
    from_debt_menu = context.user_data.get('return_to_debt_menu', False)
    list_callback = 'view_all_reminders' if from_debt_menu else 'list_reminders'

    keyboard.append([InlineKeyboardButton("🔙 Назад до списку", callback_data=list_callback)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def handle_edit_reminder(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    callback_data = update.callback_query.data
    reminder_id = int(callback_data.split('_')[-1])

    context.user_data['reminder_id'] = reminder_id

    reminder = get_reminder(user_id, reminder_id)

    if not reminder:
        await handle_list_reminders(update, context)
        return

    _, title, reminder_datetime, _, _ = reminder

    keyboard = [
        [InlineKeyboardButton("✏️ Змінити текст", callback_data='edit_reminder_title')],
        [InlineKeyboardButton("⏰ Змінити дату та час", callback_data='edit_reminder_datetime')],
        [InlineKeyboardButton("🔙 Назад", callback_data=f'view_reminder_{reminder_id}')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=f"📝 Редагування нагадування: *{title}*\n\nОберіть, що хочете змінити:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def handle_edit_reminder_title(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    reminder_id = context.user_data.get('reminder_id')

    if not reminder_id:
        await handle_list_reminders(update, context)
        return

    reminder = get_reminder(user_id, reminder_id)

    if not reminder:
        await handle_list_reminders(update, context)
        return

    _, title, _, _, _ = reminder

    keyboard = [[InlineKeyboardButton("🔙 Скасувати", callback_data=f'view_reminder_{reminder_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=f"Поточний текст: *{title}*\n\nВведіть новий текст нагадування:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    return EDIT_TITLE


async def handle_edit_reminder_title_input(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.message.from_user.id
    new_title = update.message.text

    reminder_id = context.user_data.get('reminder_id')

    if not reminder_id:
        keyboard = [[InlineKeyboardButton("🔙 Назад до нагадувань", callback_data='reminder')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text="❌ Сталася помилка. Будь ласка, спробуйте ще раз.",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    success = update_reminder(user_id, reminder_id, title=new_title)

    keyboard = [[InlineKeyboardButton("🔙 Назад до нагадування", callback_data=f'view_reminder_{reminder_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if success:
        await update.message.reply_text(
            text=f"✅ Текст нагадування успішно змінено на: *{new_title}*",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text="❌ Сталася помилка під час зміни тексту нагадування. Будь ласка, спробуйте ще раз.",
            reply_markup=reply_markup
        )

    return ConversationHandler.END


async def handle_edit_reminder_datetime(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    reminder_id = context.user_data.get('reminder_id')

    if not reminder_id:
        await handle_list_reminders(update, context)
        return

    reminder = get_reminder(user_id, reminder_id)

    if not reminder:
        await handle_list_reminders(update, context)
        return

    _, title, reminder_datetime, _, _ = reminder

    dt = datetime.strptime(reminder_datetime, "%Y-%m-%d %H:%M:%S")

    context.user_data['reminder_year'] = dt.year
    context.user_data['reminder_month'] = dt.month
    context.user_data['reminder_day'] = dt.day
    context.user_data['reminder_hour'] = dt.hour
    context.user_data['reminder_minute'] = dt.minute

    keyboard = generate_date_selection_keyboard(context)

    keyboard.append([InlineKeyboardButton("🔙 Скасувати", callback_data=f'view_reminder_{reminder_id}')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=f"Редагування нагадування: *{title}*\n\nОберіть нову дату нагадування:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    return SELECT_DATE

async def handle_edit_reminder_datetime_input(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.message.from_user.id
    datetime_text = update.message.text

    reminder_id = context.user_data.get('reminder_id')

    if not reminder_id:
        keyboard = [[InlineKeyboardButton("🔙 Назад до нагадувань", callback_data='reminder')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text="❌ Сталася помилка. Будь ласка, спробуйте ще раз.",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    try:
        reminder_datetime = datetime.strptime(datetime_text, "%Y-%m-%d %H:%M")
        reminder_datetime_str = reminder_datetime.strftime("%Y-%m-%d %H:%M:%S")

        success = update_reminder(user_id, reminder_id, reminder_datetime=reminder_datetime_str)

        keyboard = [[InlineKeyboardButton("🔙 Назад до нагадування", callback_data=f'view_reminder_{reminder_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if success:
            await update.message.reply_text(
                text=f"✅ Дата та час нагадування успішно змінені на: *{reminder_datetime.strftime('%d.%m.%Y %H:%M')}*",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text="❌ Сталася помилка під час зміни дати та часу нагадування. Будь ласка, спробуйте ще раз.",
                reply_markup=reply_markup
            )

        return ConversationHandler.END
    except ValueError:
        keyboard = [[InlineKeyboardButton("🔙 Скасувати", callback_data=f'view_reminder_{reminder_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text="❌ Некоректний формат дати та часу. Будь ласка, введіть у форматі РРРР-ММ-ДД ГГ:ХХ\nНаприклад: 2023-12-31 23:59",
            reply_markup=reply_markup
        )

        return EDIT_DATETIME

async def handle_complete_reminder(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    callback_data = update.callback_query.data
    reminder_id = int(callback_data.split('_')[-1])

    reminder = get_reminder(user_id, reminder_id)

    if not reminder:
        await handle_list_reminders(update, context)
        return

    _, title, _, _, _ = reminder

    success = mark_reminder_completed(user_id, reminder_id)

    if success:
        # Check if we're coming from the debt menu
        from_debt_menu = context.user_data.get('return_to_debt_menu', False)
        list_callback = 'view_all_reminders' if from_debt_menu else 'list_reminders'

        keyboard = [[InlineKeyboardButton("🔙 Назад до списку", callback_data=list_callback)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text=f"✅ Нагадування *{title}* відмічено як виконане.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await handle_view_reminder(update, context)

async def handle_delete_reminder(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    callback_data = update.callback_query.data
    reminder_id = int(callback_data.split('_')[-1])

    reminder = get_reminder(user_id, reminder_id)

    if not reminder:
        await handle_list_reminders(update, context)
        return

    _, title, _, _, _ = reminder

    keyboard = [
        [InlineKeyboardButton("✅ Так, видалити", callback_data=f'delete_reminder_confirm_{reminder_id}')],
        [InlineKeyboardButton("❌ Ні, скасувати", callback_data=f'view_reminder_{reminder_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=f"❓ Ви впевнені, що хочете видалити нагадування *{title}*?",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def handle_delete_reminder_confirm(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()

    callback_data = update.callback_query.data
    reminder_id = int(callback_data.split('_')[-1])

    reminder = get_reminder(user_id, reminder_id)

    if not reminder:
        await handle_list_reminders(update, context)
        return

    _, title, _, _, _ = reminder

    success = delete_reminder(user_id, reminder_id)

    if success:
        # Check if we're coming from the debt menu
        from_debt_menu = context.user_data.get('return_to_debt_menu', False)
        list_callback = 'view_all_reminders' if from_debt_menu else 'list_reminders'

        keyboard = [[InlineKeyboardButton("🔙 Назад до списку", callback_data=list_callback)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text=f"✅ Нагадування *{title}* успішно видалено.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await handle_view_reminder(update, context)

create_reminder_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(handle_create_reminder, pattern='^create_reminder$'),
        CallbackQueryHandler(handle_list_reminders, pattern='^list_reminders$'),
        CallbackQueryHandler(handle_budgeting_callback, pattern='^budgeting$')
    ],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reminder_title_input)],
        DATETIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reminder_datetime_input)],
        SELECT_DATE: [
            CallbackQueryHandler(handle_date_selection, pattern='^(date_|select_time|ignore)'),
        ],
        SELECT_TIME: [
            CallbackQueryHandler(handle_time_selection, pattern='^(hour_|minute_|back_to_date|save_reminder)'),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(handle_reminder_callback, pattern='^reminder$'),
        MessageHandler(filters.COMMAND, handle_reminder_callback)
    ],
    name="create_reminder",
    persistent=False
)

edit_reminder_title_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_edit_reminder_title, pattern='^edit_reminder_title$')],
    states={
        EDIT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_reminder_title_input)],
    },
    fallbacks=[
        CallbackQueryHandler(handle_view_reminder, pattern='^view_reminder_[0-9]+$'),
        MessageHandler(filters.COMMAND, handle_reminder_callback)
    ],
    name="edit_reminder_title",
    persistent=False
)

edit_reminder_datetime_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_edit_reminder_datetime, pattern='^edit_reminder_datetime$')],
    states={
        EDIT_DATETIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_reminder_datetime_input)],
        SELECT_DATE: [
            CallbackQueryHandler(handle_date_selection, pattern='^(date_|select_time|ignore)'),
        ],
        SELECT_TIME: [
            CallbackQueryHandler(handle_time_selection, pattern='^(hour_|minute_|back_to_date|save_reminder)'),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(handle_view_reminder, pattern='^view_reminder_[0-9]+$'),
        MessageHandler(filters.COMMAND, handle_reminder_callback)
    ],
    name="edit_reminder_datetime",
    persistent=False
)

reminder_handler = CallbackQueryHandler(handle_reminder_callback, pattern='^reminder$')
list_reminders_handler = CallbackQueryHandler(handle_list_reminders, pattern='^list_reminders$')
view_reminder_handler = CallbackQueryHandler(handle_view_reminder, pattern='^view_reminder_[0-9]+$')
edit_reminder_handler = CallbackQueryHandler(handle_edit_reminder, pattern='^edit_reminder_[0-9]+$')
complete_reminder_handler = CallbackQueryHandler(handle_complete_reminder, pattern='^complete_reminder_[0-9]+$')
delete_reminder_handler = CallbackQueryHandler(handle_delete_reminder, pattern='^delete_reminder_[0-9]+$')
delete_reminder_confirm_handler = CallbackQueryHandler(handle_delete_reminder_confirm,
                                                       pattern='^delete_reminder_confirm_[0-9]+$')

async def check_and_send_reminders(context: CallbackContext):
    from services.database_service import get_due_reminders, mark_reminder_completed

    due_reminders = get_due_reminders()

    for reminder_id, user_id, title, reminder_datetime in due_reminders:
        try:
            dt = datetime.strptime(reminder_datetime, "%Y-%m-%d %H:%M:%S")
            formatted_datetime = dt.strftime("%d.%m.%Y %H:%M")

            keyboard = [
                [InlineKeyboardButton("✅ Відмітити як виконане", callback_data=f'complete_reminder_{reminder_id}')],
                [InlineKeyboardButton("📋 Мої нагадування", callback_data='list_reminders')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=user_id,
                text=f"⏰ *НАГАДУВАННЯ*\n\n"
                     f"📝 *{title}*\n"
                     f"⏰ Час: *{formatted_datetime}*",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

            mark_reminder_completed(user_id, reminder_id)
        except Exception as e:
            print(f"Error sending reminder: {e}")
