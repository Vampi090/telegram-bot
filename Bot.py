# 🔧 Стандартные библиотеки
import os
import csv
import random
import logging
import asyncio
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timedelta, time

# 🌐 Внешние библиотеки
import requests
import matplotlib.pyplot as plt
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 🤖 Telegram Bot API
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
)

# 🔧 Логирование
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,  # Уровень логирования (INFO - выводить основные события)
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),  # Лог в файл bot.log с указанием кодировки
        logging.StreamHandler(sys.stdout)  # Лог в консоль с кодировкой utf-8
    ]
)
# Принудительно изменить кодировку sys.stdout для поддержания Unicode в консоли (если это Windows)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Создаём логгер
logger = logging.getLogger(__name__)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            amount REAL,
            category TEXT,
            type TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            user_id INTEGER,
            category TEXT,
            amount REAL,
            PRIMARY KEY (user_id, category)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            description TEXT,
            date TEXT
        )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        debtor TEXT,
        due_date TEXT,
        status TEXT
    )
""")
    conn.commit()
    conn.close()


def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📥 Управление транзакциями", callback_data='menu_transactions')],
        [InlineKeyboardButton("📊 Аналитика и отчёты", callback_data='menu_analytics')],
        [InlineKeyboardButton("🎯 Цели и бюджет", callback_data='menu_goals_budget')],
        [InlineKeyboardButton("💼 Финансовые инструменты", callback_data='menu_tools')],
        [InlineKeyboardButton("🔄 Синхронизация и экспорт", callback_data='menu_sync_export')],
        [InlineKeyboardButton("🤝 Учёт долгов", callback_data='menu_debt')],
        [InlineKeyboardButton("❓ Помощь", callback_data='menu_help')],
    ]
    return InlineKeyboardMarkup(keyboard)


def transactions_menu():
    keyboard = [
        [InlineKeyboardButton("➕ Добавить транзакцию", callback_data='add_transaction')],
        [InlineKeyboardButton("📜 История", callback_data='view_history')],
        [InlineKeyboardButton("↩️ Отменить транзакцию", callback_data='undo_transaction')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='main_menu')],
    ]
    return InlineKeyboardMarkup(keyboard)


def analytics_menu():
    keyboard = [
        [InlineKeyboardButton("📈 Статистика", callback_data='view_stats')],
        [InlineKeyboardButton("📊 Графики", callback_data='view_charts')],
        [InlineKeyboardButton("📅 Сводка", callback_data='view_report')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='main_menu')],
    ]
    return InlineKeyboardMarkup(keyboard)


def goals_budget_menu():
    keyboard = [
        [InlineKeyboardButton("🎯 Цели", callback_data='manage_goals')],
        [InlineKeyboardButton("💰 Бюджет", callback_data='manage_budget')],
        [InlineKeyboardButton("⏰ Напоминания", callback_data='manage_reminders')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='main_menu')],
    ]
    return InlineKeyboardMarkup(keyboard)


def tools_menu():
    keyboard = [
        [InlineKeyboardButton("💱 Конвертация валют", callback_data='convert_currency')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='main_menu')],
    ]
    return InlineKeyboardMarkup(keyboard)


def sync_export_menu():
    keyboard = [
        [InlineKeyboardButton("🔄 Синхронизация", callback_data='sync_data')],
        [InlineKeyboardButton("📁 Экспорт", callback_data='export_data')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='main_menu')],
    ]
    return InlineKeyboardMarkup(keyboard)


def help_menu():
    keyboard = [
        [InlineKeyboardButton("📌 Команды", callback_data='help_commands')],
        [InlineKeyboardButton("📖 Мини-гайд", callback_data='mini_guide')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='main_menu')],
    ]
    return InlineKeyboardMarkup(keyboard)



# Функция старта с обновлённым меню
async def start(update: Update, context: CallbackContext):
    await log_command_usage(update, context)
    user = update.effective_user

    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "Я помогу тебе управлять финансами: отслеживать доходы и расходы, вести бюджет, ставить цели и многое другое.\n\n"
        "Вот что я умею:\n"
        "• ➕ Добавлять транзакции (/add)\n"
        "• 📜 Показывать историю (/history)\n"
        "• 📊 Анализировать статистику (/stats)\n"
        "• 💰 Вести учет долгов (/debt)\n"
        "• 🎯 Помогать достигать финансовых целей (/goal)\n\n"
        "👇 Выберите действие:"
    )

    reply_markup = main_menu_keyboard()

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)



# Состояния диалога
AMOUNT, CATEGORY, TYPE = range(3)
WAITING_FOR_AMOUNT = 1
WAITING_FOR_NAME = ''

def generate_back_main_menu_button():
    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

async def handle_name_input(update: Update, context: CallbackContext) -> str:
    user_input = update.message.text  # Получаем текст, который ввёл пользователь

    try:
        # Преобразуем ввод в строку
        name = str(user_input)

        # Сохраняем имя во временном контексте
        context.user_data['name'] = name

        await add_transaction_final_step(update, context)

        return ConversationHandler.END

    except ValueError:
        # Обработка неправильного ввода
        await update.message.reply_text(
            "❌ Пожалуйста, введите корректное название. Попробуйте ещё раз:"
        )
        return WAITING_FOR_NAME  # Остаться в текущем состоянии


async def handle_amount_input(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text  # Получаем текст, который ввёл пользователь

    try:
        # Преобразуем ввод в число
        amount = int(user_input)

        print(f"amount {amount}")

        # Сохраняем сумму во временном контексте
        context.user_data['amount'] = amount

        # Отправляем подтверждение пользователю
        await update.message.reply_text(
            f"💾 Сумма `{amount}` сохранена!\n"
            "Введите название транзакции: ",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="add_menu")]
            ])
        )
        return WAITING_FOR_NAME

    except ValueError:
        # Обработка неправильного ввода
        await update.message.reply_text(
            "❌ Пожалуйста, введите корректное число. Попробуйте ещё раз:"
        )
        return WAITING_FOR_AMOUNT  # Остаться в текущем состоянии


async def add_transaction_final_step(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    amount = context.user_data.get('amount')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    category = context.user_data.get('name')

    print(f"category {category}")
    print(f"amount {amount}")

    transaction_type = "расход"
    if amount > 0:
        transaction_type = "доход"

    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
            INSERT INTO transactions (user_id, amount, category, type, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, amount, category, transaction_type, timestamp))

    # Проверяем, существует ли запись в таблице budget для user_id
    cursor.execute("SELECT amount FROM budget WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    # Если пользователь существует, обновить запись
    if result:
        if transaction_type == "доход":
            cursor.execute("""
                    UPDATE budget SET amount = amount + ? WHERE user_id = ? AND category = ?
                """, (amount, user_id, category))
    else:
        # Если пользователь отсутствует - создать новую запись
        initial_amount = amount if transaction_type == "доход" else -abs(amount)
        cursor.execute("""
                INSERT INTO budget (user_id, amount, category) VALUES (?, ?)
            """, (user_id, initial_amount, category))

    conn.commit()
    conn.close()

    # Подтверждение успешного добавления + главное меню
    await update.message.reply_text(
        f"✅ Транзакция добавлена:\n💰 {amount} | 📂 {category} | 🔹 {transaction_type}",
        reply_markup=main_menu_keyboard()
    )


async def simple_menu_button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "help":
        help_text = (
            "❓ *Справка по командам:*\n\n"
            "• `/add сумма категория` — добавить транзакцию\n"
            "• `/history` — история транзакций\n"
            "• `/stats` — статистика расходов\n"
            "• `/goal` — финансовые цели\n"
            "• `/debt` — долги и займы\n"
            "• `/budget` — установка бюджета\n"
            "• `/convert` — конвертация валют\n\n"
            "👇 Вы можете также использовать кнопки ниже для быстрого доступа."
        )
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=main_menu_keyboard())

    #elif data == "add_menu":
    #    await query.edit_message_text(
    #        "✍️ *Добавление транзакции:*\n\n"
    #        "Введите команду в формате:\n"
    #        "`/add сумма категория`\n\n"
    #        "*Пример:* `/add 500 еда`",
    #        parse_mode="Markdown",
    #        reply_markup=main_menu_keyboard()
    #    )

    elif data == "add_menu":
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "✍️ *Введите сумму:*\n\n"
            "*Пример:* `500` для сохранения дохода"
            " или `-500` если хотите сохранить расход",
            parse_mode="Markdown",
            reply_markup=generate_back_main_menu_button()
        )
        return WAITING_FOR_AMOUNT

    elif data == "history":
        # Предположим, ты хочешь показывать placeholder здесь
        await query.edit_message_text(
            "📜 *История транзакций:*\n\n(Здесь будет ваша история)",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )

    elif data == "stats":
        await query.edit_message_text(
            "📊 *Статистика расходов:*\n\n(Здесь будет ваша статистика по категориям)",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )

    elif data == "goal":
        await query.edit_message_text(
            "🎯 *Финансовые цели:*\n\n(Установите и отслеживайте цели)",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )

    elif data == "budget":
        await query.edit_message_text(
            "💸 *Бюджет:*\n\n(Установите лимит бюджета с помощью `/budget 10000`)",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )

    elif data == "convert":
        await query.edit_message_text(
            "💱 *Конвертация валют:*\n\n"
            "Введите в формате: `/convert 100 USD EUR`",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )

    elif data == "debt":
        await debt(update, context)

    elif data == "main_menu":
        await query.edit_message_text("🏠 *Главное меню:*", parse_mode="Markdown", reply_markup=main_menu_keyboard())



async def add_transaction(update: Update, context: CallbackContext):
    """Обработка команды /add"""
    message = update.message  # Сообщение пользователя

    if not message or not context.args:  # Проверяем, есть ли сообщение и аргументы
        if message:  # Только если пользователь сам ввел неверный формат
            await message.reply_text(
                "⚠️ Неверный формат! Используйте: `/add сумма категория`\nПример: `/add 500 еда`",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard()
            )
        return

    try:
        amount = float(context.args[0])  # Парсим сумму
    except ValueError:
        await message.reply_text(
            "❌ Ошибка! Введите корректную сумму.",
            reply_markup=main_menu_keyboard()
        )
        return

    category = " ".join(context.args[1:])  # Склеиваем все оставшиеся слова в категорию
    transaction_type = "расход"  # Устанавливаем тип как расход по умолчанию

    # Убедимся, что если сумма положительная, это доход
    if amount > 0:
        transaction_type = "доход"

    user_id = update.effective_user.id
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Записываем в БД
    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (user_id, amount, category, type, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, amount, category, transaction_type, timestamp))
    conn.commit()
    conn.close()

    # Подтверждение успешного добавления + главное меню
    await message.reply_text(
        f"✅ Транзакция добавлена:\n💰 {amount} | 📂 {category} | 🔹 {transaction_type}",
        reply_markup=main_menu_keyboard()
    )


async def add_type(update: Update, context: CallbackContext):
    """Обработка выбора типа транзакции и сохранение в БД"""
    query = update.callback_query
    await query.answer()

    context.user_data['type'] = query.data

    user_id = update.effective_user.id
    amount = context.user_data.get('amount')
    category = context.user_data.get('category')
    transaction_type = context.user_data.get('type')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Подключаемся к БД и сохраняем данные
    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()

    # Запись транзакции в БД
    cursor.execute("""
        INSERT INTO transactions (user_id, amount, category, type, timestamp) 
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, amount, category, transaction_type, timestamp))

    # Обновление бюджета
    if transaction_type == "расход":
        cursor.execute("""
            UPDATE budget SET amount = amount - ? WHERE user_id = ?
        """, (amount, user_id))
    elif transaction_type == "доход":
        cursor.execute("""
            UPDATE budget SET amount = amount + ? WHERE user_id = ?
        """, (amount, user_id))

    conn.commit()
    conn.close()

    # Подтверждение и отображение главного меню
    await query.message.edit_text(
        f"✅ Транзакция добавлена:\n💰 {amount} | 📂 {category} | 🔹 {transaction_type}",
        reply_markup=main_menu_keyboard()
    )

    return ConversationHandler.END  # Завершаем диалог

        # Функция помощи (список команд)
async def help_command(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    help_text = """
📌 *Доступные команды:*
/start — Запуск бота  
/add [сумма] [категория] — Добавить транзакцию  
/history — История транзакций  
/stats — Статистика расходов  
/goal — Управление целями  
/undo — Отмена последней транзакции  
/export — Экспорт данных  
/chart — Графики расходов  
/reminder — Напоминания о бюджете  
/budget — Управление бюджетом  
/convert — Конвертация валют  
/sync — Синхронизация с Google Таблицами  
/report [месяц] — Сводка за месяц  
/debt — Учет долгов
"""

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=help_text,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
    elif update.message:
        await update.message.reply_text(
            help_text,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )

# Функция работы с целями
async def goal(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.effective_user.id
    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()

    args = context.args if update.message else []

    if len(args) >= 2:
        try:
            amount = float(args[0])
            description = " ".join(args[1:])
            cursor.execute(
                "INSERT INTO goals (user_id, amount, description, date) VALUES (?, ?, ?, datetime('now'))",
                (user_id, amount, description)
            )
            conn.commit()
            text = f"✅ Додано нову ціль: {amount}₴ - {description}"
        except ValueError:
            text = "❌ Помилка: некоректна сума. Введіть число."
    else:
        cursor.execute("SELECT amount, description, date FROM goals WHERE user_id = ? ORDER BY date DESC", (user_id,))
        goals = cursor.fetchall()
        if goals:
            text = "🎯 *Ваші фінансові цілі:*\n"
            for g in goals:
                text += f"💰 {g[1]} - {g[0]}₴ (Додано: {g[2]})\n"
        else:
            text = "📌 У вас поки що немає фінансових цілей."

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
    elif update.message:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )

    conn.close()

# Функция конвертации валют
async def convert(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    args = context.args if update.message else []

    if len(args) < 2:
        text = "❌ Неправильний формат. Приклад: /convert 100 USD EUR"
    else:
        try:
            amount = float(args[0])
            from_currency = args[1].upper()
            to_currency = args[2].upper() if len(args) > 2 else "UAH"

            rate = await get_exchange_rate(from_currency, to_currency)
            if rate is None:
                text = f"❌ Не вдалося отримати курс для {from_currency} → {to_currency}."
            else:
                converted_amount = round(amount * rate, 2)
                text = f"💱 {amount} {from_currency} ≈ {converted_amount} {to_currency}"

        except ValueError:
            text = "❌ Невірний формат числа."
        except Exception as e:
            print(f"Ошибка в convert: {e}")
            text = "⚠️ Виникла помилка при конвертації. Спробуйте ще раз."

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=main_menu_keyboard()
        )
    elif update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=main_menu_keyboard()
        )

# Функция получения курса валют (асинхронная + улучшенная обработка ошибок)
async def get_exchange_rate(from_currency, to_currency):
    """Получает курс обмена между двумя валютами через exchangerate-api"""
    url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        rates = data.get("rates", {})
        rate = rates.get(to_currency)

        if rate is None:
            print(f"[Курс валют] ❌ Не найден курс: {from_currency} → {to_currency}")
            return None

        print(f"[Курс валют] 💱 Курс {from_currency} → {to_currency} = {rate}")
        return rate

    except requests.exceptions.Timeout:
        print("[Курс валют] ⏱ Таймаут при получении курса.")
    except requests.exceptions.RequestException as e:
        print(f"[Курс валют] ⚠️ Ошибка запроса: {e}")

    return None

    # Функция просмотра истории транзакций (последние 10 операций)
async def history(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = None
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        await update.callback_query.answer()  # Закрываем "часики"

    if not user_id:
        return

    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, amount, category, type FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT 10
    """, (user_id,))
    transactions = cursor.fetchall()
    conn.close()

    if not transactions:
        text = "📜 У вас еще нет транзакций."
    else:
        text = "📝 *История транзакций (последние 10):*\n"
        for date, amount, category, t_type in transactions:
            text += f"📅 {date} | 💰 {amount} грн | 📂 {category} ({t_type})\n"

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
    elif update.message:
        await update.message.reply_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )

    # Функция просмотра статистики расходов
async def stats(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = None
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        await update.callback_query.answer()  # Закрываем "часики"

    if not user_id:
        return

    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, SUM(amount) FROM transactions
        WHERE user_id = ? AND type = 'расход'
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """, (user_id,))
    
    stats_data = cursor.fetchall()
    conn.close()

    if not stats_data:
        text = "📊 У вас еще нет данных о расходах."
    else:
        text = "📊 *Статистика расходов по категориям:*\n"
        for category, total in stats_data:
            text += f"🔹 {category}: {round(total, 2)} грн\n"

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
    elif update.message:
        await update.message.reply_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )

    # Функция установки и просмотра целей
async def goal(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = None
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        await update.callback_query.answer()

    if not user_id:
        return

    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()

    # Добавление цели
    if context.args and len(context.args) >= 2:
        try:
            amount = float(context.args[0])
            description = " ".join(context.args[1:])
            cursor.execute("""
                INSERT INTO goals (user_id, amount, description, date)
                VALUES (?, ?, ?, date('now'))
            """, (user_id, amount, description))
            conn.commit()
            conn.close()

            text = f"🎯 Цель '{description}' на сумму {amount} грн установлена!"
        except ValueError:
            conn.close()
            text = "❌ Неверный формат! Используйте: /goal [сумма] [описание]"

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=main_menu_keyboard()
            )
        else:
            await update.message.reply_text(text, reply_markup=main_menu_keyboard())
        return

    # Показ целей
    cursor.execute("""
        SELECT amount, description, date FROM goals
        WHERE user_id = ?
        ORDER BY date DESC
    """, (user_id,))
    goals = cursor.fetchall()
    conn.close()

    if not goals:
        text = "🎯 У вас пока нет финансовых целей."
    else:
        text = "🎯 *Ваши финансовые цели:*\n"
        for amount, description, date in goals:
            text += f"🔹 {description}: {amount} грн (дата: {date})\n"

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )

    # Функция отмены последней транзакции
async def undo(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.message.from_user.id
    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()

    # Получаем последнюю транзакцию
    cursor.execute("""
        SELECT id, amount, category, type FROM transactions 
        WHERE user_id = ? 
        ORDER BY date DESC LIMIT 1
    """, (user_id,))
    
    last_transaction = cursor.fetchone()

    if not last_transaction:
        await update.message.reply_text(
            "❌ У вас нет транзакций для отмены.",
            reply_markup=main_menu_keyboard()
        )
        conn.close()
        return

    transaction_id, amount, category, transaction_type = last_transaction

    # Удаляем транзакцию
    cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))

    # Возвращаем сумму в бюджет
    if transaction_type == "расход":
        cursor.execute("UPDATE budget SET amount = amount + ? WHERE user_id = ?", (amount, user_id))
    elif transaction_type == "доход":
        cursor.execute("UPDATE budget SET amount = amount - ? WHERE user_id = ?", (amount, user_id))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ Отменена последняя транзакция: {category} на {amount} грн ({transaction_type}).",
        reply_markup=main_menu_keyboard()
    )

# Функция экспорта данных в CSV
async def export_data(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    # Определяем user_id
    user_id = update.effective_user.id

    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()

    # Получаем все транзакции пользователя
    cursor.execute("""
        SELECT date, amount, category, type FROM transactions 
        WHERE user_id = ?
        ORDER BY date DESC
    """, (user_id,))
    
    transactions = cursor.fetchall()
    conn.close()

    if not transactions:
        await context.bot.send_message(chat_id=user_id, text="❌ У вас нет данных для экспорта.")
        return

    file_path = f"transactions_{user_id}.csv"

    # Создаём CSV файл
    with open(file_path, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Дата", "Сумма", "Категория", "Тип"])
        writer.writerows(transactions)

    # Отправляем CSV пользователю
    with open(file_path, "rb") as doc:
        await context.bot.send_document(
            chat_id=user_id,
            document=doc,
            filename=f"transactions_{user_id}.csv",
            caption="📁 Ваши данные экспортированы.",
            reply_markup=main_menu_keyboard()
        )

    os.remove(file_path)


# Функция построения графика расходов

import matplotlib.pyplot as plt
import os

async def show_chart(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.effective_user.id

    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()

    # Получаем данные о расходах пользователя
    cursor.execute("""
        SELECT category, SUM(amount) FROM transactions 
        WHERE user_id = ? AND type = 'расход' 
        GROUP BY category
    """, (user_id,))
    
    data = cursor.fetchall()
    conn.close()

    if not data:
        await context.bot.send_message(chat_id=user_id, text="❌ Недостаточно данных для графика.")
        return

    # Разбираем данные
    categories, amounts = zip(*data) if len(data) > 1 else ([data[0][0]], [data[0][1]])

    # Убираем отрицательные значения расходов
    amounts = [abs(amount) for amount in amounts]

    # Строим график
    plt.figure(figsize=(10, 6))
    bars = plt.bar(categories, amounts, color=["#4CAF50", "#FF9800", "#2196F3", "#9C27B0", "#E91E63"])

    # Добавляем проценты над столбцами
    total = sum(amounts)
    for bar in bars:
        yval = bar.get_height()
        percent = (yval / total) * 100
        plt.text(bar.get_x() + bar.get_width() / 2, yval + 10, f"{percent:.1f}%", ha='center', va='bottom')

    # Подписи
    plt.title("📊 Распределение расходов по категориям")
    plt.xlabel("Категория")
    plt.ylabel("Сумма (грн)")
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)

    # Сохранение графика
    file_path = f"chart_{user_id}.png"
    plt.tight_layout()
    plt.savefig(file_path)
    plt.close()

    # Отправка графика
    with open(file_path, "rb") as photo:
        await context.bot.send_photo(chat_id=user_id, photo=photo, caption="📊 Ваш график расходов.")

    os.remove(file_path)  # Удаляем после отправки


# Функция установки напоминания

from datetime import datetime, timedelta
import asyncio

async def set_reminder(update: Update, context: CallbackContext):
    """Устанавливает напоминание о превышении суммы расходов."""
    await log_command_usage(update, context)

    user_id = update.effective_user.id
    args = context.args if update.message else update.callback_query.data.split()[1:]

    if not args or len(args) < 2:
        await context.bot.send_message(chat_id=user_id, text="❌ Использование: /reminder [сумма] [время в часах]")
        return

    try:
        amount = float(args[0])
        hours = int(args[1])
        remind_time = datetime.now() + timedelta(hours=hours)

        # Сохранение в БД
        try:
            conn = sqlite3.connect("finance_bot.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reminders (user_id, amount, remind_time) 
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET amount = excluded.amount, remind_time = excluded.remind_time
            """, (user_id, amount, remind_time))
            conn.commit()
            conn.close()
        except Exception as e:
            await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка БД: {str(e)}")
            return

        # Планирование задачи в job_queue
        job_name = f"reminder_{user_id}"
        context.job_queue.run_once(reminder_callback, when=timedelta(hours=hours), context={"user_id": user_id, "amount": amount}, name=job_name)

        await context.bot.send_message(chat_id=user_id, text=f"⏳ Напоминание установлено: {amount} грн через {hours} ч.")

    except ValueError:
        await context.bot.send_message(chat_id=user_id, text="❌ Неверный формат. Используйте: /reminder [сумма] [время в часах]")

async def reminder_callback(context: CallbackContext):
    """Функция для отправки напоминания."""
    job = context.job
    user_id = job.context["user_id"]
    amount = job.context["amount"]

    await context.bot.send_message(chat_id=user_id, text=f"🔔 Напоминание! Ваш лимит {amount} грн приближается. Проверьте расходы.")


async def schedule_reminder(user_id, amount, remind_time, context):
    """Асинхронная задержка и отправка напоминания"""
    wait_time = (remind_time - datetime.now()).total_seconds()
    if wait_time > 0:
        await asyncio.sleep(wait_time)

    # Проверка: не изменилось ли напоминание в базе
    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT remind_time FROM reminders WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        db_remind_time = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        if db_remind_time == remind_time:
            await context.bot.send_message(chat_id=user_id, text=f"🔔 Напоминание! Вы планировали потратить {amount} грн.")

        # Функция отслеживания прогресса по целям
async def track_goals(update: Update, context: CallbackContext):
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

    try:
        conn = sqlite3.connect("finance_bot.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT amount, description, date FROM goals 
            WHERE user_id = ? ORDER BY date DESC
        """, (user_id,))
        goals = cursor.fetchall()
    finally:
        conn.close()

    if not goals:
        await context.bot.send_message(chat_id=user_id, text="🎯 У вас пока нет установленных целей.")
        return

    message_lines = ["📌 *Ваши финансовые цели:*"]
    for amount, description, date in goals:
        message_lines.append(f"💰 {description}: {amount} грн (установлено {date})")

    message = "\n".join(message_lines)
    await context.bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")


    # Функция фильтрации транзакций по категории и типу
async def filter_transactions(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.message.from_user.id
    args = context.args

    if not args:
        await update.message.reply_text("❌ Укажите категорию или тип. Пример: `/transactions Продукты`")
        return

    filter_param = " ".join(args)  # Объединяем аргументы в строку (если фильтр состоит из нескольких слов)

    try:
        conn = sqlite3.connect("finance_bot.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT date, amount, category, type FROM transactions
            WHERE user_id = ? AND (LOWER(category) = LOWER(?) OR LOWER(type) = LOWER(?))
            ORDER BY date DESC
            LIMIT 20
        """, (user_id, filter_param, filter_param))
        transactions = cursor.fetchall()
    finally:
        conn.close()

    if not transactions:
        await update.message.reply_text(f"🔍 Транзакции по фильтру '*{filter_param}*' не найдены.", parse_mode="Markdown")
        return

    message_lines = [f"📂 *Транзакции по фильтру:* `{filter_param}`"]
    for date, amount, category, type_ in transactions:
        message_lines.append(f"📅 `{date}` | 💰 `{amount} грн` | 🏷️ {category} ({type_})")

    message = "\n".join(message_lines)
    await update.message.reply_text(message, parse_mode="Markdown")


    # Функция установки и просмотра бюджета
async def budget(update: Update, context: CallbackContext):
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
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ])

    try:
        conn = sqlite3.connect("finance_bot.db")
        cursor = conn.cursor()

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

            cursor.execute("""
                INSERT INTO budget (user_id, category, amount)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, category) DO UPDATE SET amount = ?
            """, (user_id, category, amount, amount))
            conn.commit()

            msg = await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Бюджет для категории '*{category}*' установлен: *{amount} грн*",
                parse_mode="Markdown",
                reply_markup=back_button_markup
            )
            context.user_data['budget_message_id'] = msg.message_id

        else:
            # Просмотр бюджета
            cursor.execute("SELECT category, amount FROM budget WHERE user_id = ?", (user_id,))
            budgets = cursor.fetchall()

            if not budgets:
                msg = await context.bot.send_message(
                    chat_id=user_id,
                    text="💡 У вас пока нет установленного бюджета.",
                    reply_markup=back_button_markup
                )
                context.user_data['budget_message_id'] = msg.message_id
                return

            message_lines = ["📊 *Ваши бюджеты:*"]
            for category, amount in budgets:
                message_lines.append(f"💰 *{category}*: `{amount} грн`")

            msg = await context.bot.send_message(
                chat_id=user_id,
                text="\n".join(message_lines),
                parse_mode="Markdown",
                reply_markup=back_button_markup
            )
            context.user_data['budget_message_id'] = msg.message_id

    finally:
        conn.close()


async def close_budget_if_active(update: Update, context: CallbackContext):
    # Проверяем, если активное сообщение бюджета существует
    print("test 1")
    if context.user_data.get('budget_message_id'):
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id,
                                             message_id=context.user_data['budget_message_id'])
        except Exception:
            pass  # Игнорируем ошибки, если сообщение уже удалено

        # Сбрасываем состояние
        context.user_data['budget_message_id'] = None


async def advice(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    tips = [
        "💡 Ведите учет доходов и расходов, чтобы лучше контролировать финансы.",
        "📉 Откладывайте не менее 10% дохода на сбережения.",
        "🛒 Планируйте покупки заранее, чтобы избежать лишних трат.",
        "💳 Не используйте кредитные деньги на ненужные вещи.",
        "📈 Инвестируйте часть дохода в долгосрочные активы.",
        "💰 Ставьте финансовые цели и следите за их выполнением.",
        "🔄 Пересматривайте бюджет раз в месяц, чтобы корректировать расходы."
    ]

    tip = random.choice(tips)
    await update.effective_message.reply_text(tip)


    # Функция синхронизации с Google Таблицами
async def sync(update: Update, context: CallbackContext):
    await log_command_usage(update, context)

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    await context.bot.send_message(chat_id=chat_id, text="🔄 Синхронизация данных запущена...")

    try:
        # Подключение к Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
        client = gspread.authorize(creds)

        spreadsheet_id = "ВАШ_SPREADSHEET_ID"  # <-- Заменить на ваш
        sheet = client.open_by_key(spreadsheet_id).sheet1

        # Получаем транзакции пользователя
        conn = sqlite3.connect("finance_bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT date, amount, category, type FROM transactions WHERE user_id = ?", (user_id,))
        transactions = cursor.fetchall()
        conn.close()

        if not transactions:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ У вас нет транзакций для синхронизации.")
            return

        # Обновление таблицы
        sheet.clear()
        sheet.append_row(["Дата", "Сумма", "Категория", "Тип"])
        sheet.append_rows(transactions)

        await context.bot.send_message(chat_id=chat_id, text="✅ Данные успешно синхронизированы с Google Таблицами!")

    except Exception as e:
        logger.error(f"Ошибка при синхронизации: {e}")
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Ошибка при синхронизации: {str(e)}")


async def log_command_usage(update: Update, context: CallbackContext):
    user = update.effective_user
    if not user:
        return

    user_id = user.id
    username = user.username if user.username else "N/A"
    full_name = user.full_name
    command = None
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if update.message:
        command = update.message.text.split()[0]
        timestamp = update.message.date.strftime("%Y-%m-%d %H:%M:%S")
    elif update.callback_query:
        command = update.callback_query.data

    if not command:
        return

    # Подключаемся к базе данных
    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()

    # Пересоздаём таблицу с учетом username
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS command_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            command TEXT,
            timestamp TEXT
        )
    """)

    # Вставляем данные в новую таблицу
    cursor.execute("""
        INSERT INTO command_logs (user_id, username, full_name, command, timestamp) 
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, username, full_name, command, timestamp))

    conn.commit()
    conn.close()

    logger.info(f"Команда {command} была вызвана пользователем {user_id} ({username})")

def save_debt_to_db(user_id, name, amount):
    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            amount REAL,
            status TEXT DEFAULT 'open',
            timestamp TEXT
        )
    """)
    cursor.execute("""
        INSERT INTO debts (user_id, name, amount, timestamp)
        VALUES (?, ?, ?, datetime('now'))
    """, (user_id, name, float(amount)))
    conn.commit()
    conn.close()

def get_debts_from_db(user_id):
    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, amount FROM debts WHERE user_id = ? AND status = 'open'", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"name": row[0], "amount": row[1]} for row in rows]

def get_debt_history(user_id):
    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, amount, status, timestamp FROM debts WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [f"{row[0]}: {row[1]}₽ ({row[2]}) — {row[3]}" for row in rows]

# ---------- ХЕНДЛЕРЫ ----------

async def debt(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📜 Мои долги", callback_data="view_debts")],
        [InlineKeyboardButton("➕ Добавить долг", callback_data="add_debt")],
        [InlineKeyboardButton("📚 История долгов", callback_data="debt_history")],
        [InlineKeyboardButton("✅ Закрыть долг", callback_data="close_debt")],
        [InlineKeyboardButton("🔔 Напоминание", callback_data="remind_debt")],
        [InlineKeyboardButton("🆘 Помощь", callback_data="help_debt")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("💼 Управление долгами:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("💼 Управление долгами:", reply_markup=reply_markup)

async def debt_menu_button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    user_id = query.from_user.id

    if query.data == "view_debts":
        debts = get_debts_from_db(user_id)
        text = (
            "📜 Ваши долги:\n" + "\n".join(f"{d['name']}: {d['amount']}₽" for d in debts)
            if debts else "✅ У вас нет долгов."
        )
        await query.message.edit_text(text, reply_markup=generate_back_button())


    elif query.data == "debt_history":
        history = get_debt_history(user_id)
        text = (
            "📚 История долгов:\n" + "\n".join(history)
            if history else "История пуста."
        )
        await query.message.edit_text(text, reply_markup=generate_back_button())

    elif query.data == "close_debt":
        await query.message.edit_text(
            "✅ Укажите, какой долг вы хотите закрыть (введите имя и сумму):",
            reply_markup=generate_back_button()
        )

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

    elif query.data == "main_menu":
        await query.message.delete()
        await start(update, context)

    elif query.data == "add_debt":
        text = (
            "➕ *Как добавить долг:*\n\n"
            "Вы можете добавить долг вручную с помощью команды:\n"
            "`/adddebt Имя Сумма`\n\n"
            "*Пример:* `/adddebt Алексей 3000`\n"
            "Это создаст запись о долге в вашу базу данных."
        )
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=generate_back_button())

    elif query.data == "debt_back":
        print("Кнопка 'Назад' нажата")
        await debt(update, context)

async def ask_debt_name(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Введите имя человека, которому вы должны или который должен вам:")
    return DEBT_NAME

async def ask_debt_amount(update: Update, context: CallbackContext):
    context.user_data["debt_name"] = update.message.text
    await update.message.reply_text("Введите сумму долга:")
    return DEBT_AMOUNT

async def save_debt(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    debt_name = context.user_data.get("debt_name")
    try:
        amount = float(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Введите корректное число.")
        return DEBT_AMOUNT

    save_debt_to_db(user_id, debt_name, amount)
    await update.message.reply_text(f"✅ Долг сохранён: {debt_name} — {amount}₽")
    return ConversationHandler.END

async def cancel_add_debt(update: Update, context: CallbackContext):
    await update.message.reply_text("🚫 Добавление долга отменено.")
    return ConversationHandler.END

def send_debt_reminder(context: CallbackContext):
    job = context.job
    user_id = job.chat_id
    debts = get_debts_from_db(user_id)
    if debts:
        text = "🔔 Напоминание о долгах:\n" + "\n".join(f"{d['name']}: {d['amount']}₽" for d in debts)
        context.bot.send_message(chat_id=user_id, text=text)

async def set_daily_reminder(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    context.job_queue.run_daily(
        send_debt_reminder,
        time=datetime.time(hour=9, minute=0),
        chat_id=chat_id,
        name=str(chat_id)
    )
    await update.callback_query.message.reply_text("✅ Напоминания будут приходить каждый день в 9:00.")

async def adddebt(update: Update, context: CallbackContext):
    try:
        _, name, amount = update.message.text.split(maxsplit=2)
        save_debt_to_db(update.effective_user.id, name, float(amount))
        await update.message.reply_text(f"✅ Долг добавлен: {name} — {amount}₽")
    except ValueError:
        await update.message.reply_text("❌ Формат: `/adddebt имя сумма`\nПример: `/adddebt Алексей 3000`", parse_mode="Markdown")

def generate_back_button():
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="debt_back")]]
    return InlineKeyboardMarkup(keyboard)


# Функция логирования использования команд
async def log_command_usage(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id if user else None
    username = user.username if user and user.username else "—"
    full_name = user.full_name if user else "—"

    if not user_id:
        return  # Нет пользователя — не логируем

    # Определяем команду
    command = None
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if update.message:
        command = update.message.text.split()[0]
        timestamp = update.message.date.strftime("%Y-%m-%d %H:%M:%S")
    elif update.callback_query:
        command = update.callback_query.data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not command:
        return

    # Сохраняем в БД
    conn = sqlite3.connect("finance_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS command_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            command TEXT,
            timestamp TEXT
        )
    """)
    cursor.execute(
        "INSERT INTO command_logs (user_id, username, full_name, command, timestamp) VALUES (?, ?, ?, ?, ?)",
        (user_id, username, full_name, command, timestamp)
    )
    conn.commit()
    conn.close()

    logger.info(f"📥 {full_name} (@{username}, ID: {user_id}) вызвал команду: {command} в {timestamp}")

    # Функция обработки нажатий кнопок
# ВАЖНО: Убедись, что log_command_usage импортирован выше или находится в этом же файле
from datetime import time

async def main_menu_button_handler(update: Update, context: CallbackContext):
    await log_command_usage(update, context)  # 🔥 Логирование кнопок
    query = update.callback_query
    await query.answer()

    data = query.data

    # 🔹 Переход в подменю
    if data == 'transactions':
        await query.edit_message_text("📥 Меню транзакцій:", reply_markup=transaction_menu_keyboard())
    elif data == 'analytics':
        await query.edit_message_text("📊 Аналітика та звіти:", reply_markup=analytics_menu_keyboard())
    elif data == 'budgeting':
        await query.edit_message_text("🎯 Цілі та бюджет:", reply_markup=budget_menu_keyboard())
    elif data == 'tools':
        await query.edit_message_text("💼 Фінансові інструменти:", reply_markup=tools_menu_keyboard())
    elif data == 'sync_export':
        await query.edit_message_text("🔄 Синхронізація та експорт:", reply_markup=sync_menu_keyboard())
    elif data == 'help_section':
        await query.edit_message_text("❓ Допомога:", reply_markup=help_menu_keyboard())

    # 🔹 Управление транзакциями
    elif data == 'add':
        await add_transaction(update, context)
    elif data == 'history':
        await history(update, context)
    elif data == 'undo':
        await undo(update, context)  # не забудь реализовать эту функцию
    elif data == 'stats':
        await stats(update, context)

    # 🔹 Цели и бюджет
    elif data == 'budget':
        await budget(update, context)
    elif data == 'goal':
        await goal(update, context)

    # 🔹 Графики и статистика
    elif data == 'chart':
        await show_chart(update, context)
    elif data == 'report':
        await track_goals(update, context)

    # 🔹 Финансовые инструменты
    elif data == 'convert':
        await convert(update, context)

    # 🔹 Синхронизация и экспорт
    elif data == 'sync':
        await sync(update, context)
    elif data == 'export':
        await export_data(update, context)

    # 🔹 Напоминания
    elif data == 'reminder':
        await set_reminder(update, context)

    # 🔹 Учёт долгов
    elif data == 'debt':
        await debt(update, context)

    # 🔹 Помощь
    elif data == 'help':
        await help_command(update, context)
    elif data == 'guide':
        await query.edit_message_text("📖 Мінi-гайд:\n\n1. Додайте транзакцію через ➕\n2. Перегляньте статистику\n3. Встановіть бюджет або ціль\n\nПочніть з головного меню: /start", reply_markup=help_menu_keyboard())

    # 🔹 Возврат в главное меню
    elif data == 'main_menu':
        await query.edit_message_text("🏠 Головне меню:", reply_markup=main_menu_keyboard())

    # ❌ Обработка ошибок
    else:
        await query.edit_message_text("❌ Невідома команда.", reply_markup=main_menu_keyboard())




# Главное меню
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Транзакції", callback_data='transactions')],
        [InlineKeyboardButton("📊 Аналітика та звіти", callback_data='analytics')],
        [InlineKeyboardButton("🎯 Цілі та бюджет", callback_data='budgeting')],
        [InlineKeyboardButton("💼 Фінансові інструменти", callback_data='tools')],
        [InlineKeyboardButton("🔄 Синхронізація та експорт", callback_data='sync_export')],
        [InlineKeyboardButton("🤝 Облік боргів", callback_data='debt')],
        [InlineKeyboardButton("❓ Допомога", callback_data='help_section')],
    ])

# Подменю: Управление транзакциями
def transaction_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Додати транзакцію", callback_data='add')],
        [InlineKeyboardButton("📜 Історія", callback_data='history')],
        [InlineKeyboardButton("↩️ Відміна транзакції", callback_data='undo')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ])

# Подменю: Аналитика и отчеты
def analytics_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Статистика", callback_data='stats')],
        [InlineKeyboardButton("📊 Графіки", callback_data='chart')],
        [InlineKeyboardButton("📅 Звіт", callback_data='report')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ])

# Подменю: Цели и бюджет
def budget_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Цілі", callback_data='goal')],
        [InlineKeyboardButton("💰 Бюджет", callback_data='budget')],
        [InlineKeyboardButton("⏰ Нагадування", callback_data='reminder')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ])

# Подменю: Финансовые инструменты
def tools_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💱 Конвертація валют", callback_data='convert')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ])

# Подменю: Синхронизация и экспорт
def sync_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Синхронізація з Google Таблицями", callback_data='sync')],
        [InlineKeyboardButton("📁 Експорт даних", callback_data='export')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ])

# Подменю: Помощь
def help_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 Команди", callback_data='help')],
        [InlineKeyboardButton("📖 Гайд", callback_data='guide')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ])



# Запуск бота
if __name__ == "__main__":
    init_db()
    TOKEN = "7888156941:AAGeuOWwEYSZwjOv1aY5eKUcPMxJlTPANuk"
    app = Application.builder().token(TOKEN).build()

    # Обработчики команд
    app.add_handler(CommandHandler("start", start), group=0)
    app.add_handler(CommandHandler("add", add_transaction), group=0)
    app.add_handler(CommandHandler("history", history), group=0)
    app.add_handler(CommandHandler("debt", debt), group=0)  # логирование внутри самой функции debt
    app.add_handler(CommandHandler("stats", stats), group=0)
    app.add_handler(CommandHandler("goal", goal), group=0)
    app.add_handler(CommandHandler("undo", undo), group=0)
    app.add_handler(CommandHandler("export", export_data), group=0)
    app.add_handler(CommandHandler("chart", show_chart), group=0)
    app.add_handler(CommandHandler("help", help_command), group=0)
    app.add_handler(CommandHandler("reminder", set_reminder), group=0)
    app.add_handler(CommandHandler("goaltrack", track_goals), group=0)
    app.add_handler(CommandHandler("transactions", filter_transactions), group=0)
    app.add_handler(CommandHandler("budget", budget), group=0)
    app.add_handler(CommandHandler("advice", advice), group=0)
    app.add_handler(CommandHandler("convert", convert), group=0)
    app.add_handler(CommandHandler("sync", sync), group=0)
    app.add_handler(CommandHandler("adddebt", adddebt), group=0)
    app.add_handler(CallbackQueryHandler(start, pattern="^main_menu$"), group=0)

    # ConversationHandler для долгов
    DEBT_NAME, DEBT_AMOUNT = range(2)
    debt_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_debt_name, pattern="^add_debt$")],
        states={
            DEBT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_debt_amount),
                CallbackQueryHandler(debt_menu_button_handler)
            ],
            DEBT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_debt),
                CallbackQueryHandler(debt_menu_button_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_add_debt)],
    )
    app.add_handler(debt_conv_handler, group=0)

    # Общий conversation handler (например, для add_menu/convert/help)
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(simple_menu_button_handler, pattern="^(add_menu|convert|help)$")],
        states={
            WAITING_FOR_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_input),
                CallbackQueryHandler(debt_menu_button_handler)
            ],
            WAITING_FOR_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_input),
                CallbackQueryHandler(debt_menu_button_handler)
            ],
        },
        fallbacks=[CallbackQueryHandler(start, pattern="^main_menu$")]
    )
    app.add_handler(conv_handler, group=0)

    # Специфические обработчики кнопок
    app.add_handler(CallbackQueryHandler(debt_menu_button_handler, pattern="^(view_debts|debt_history|close_debt|remind_debt|help_debt|main_menu|add_debt|debt_back)$"), group=0)
    app.add_handler(CallbackQueryHandler(main_menu_button_handler, pattern="^(add|history|stats|budget|goal|chart|convert|export|sync|reminder|report|debt|help)$"), group=0)
    app.add_handler(CallbackQueryHandler(simple_menu_button_handler, pattern="^(add_menu|convert|help)$"), group=0)

    # 🆕 Универсальный обработчик callback-кнопок (ставим последним!)
    app.add_handler(CallbackQueryHandler(main_menu_button_handler), group=0)

    # Планировщик задач
    job_queue = app.job_queue
    job_queue.run_daily(lambda context: context.job_queue.run_once(set_reminder, 0), time=time(9, 0))

    # Закрытие меню бюджета, если нужно
    app.add_handler(MessageHandler(filters.ALL, close_budget_if_active), group=1)

    # Обработка ошибок
    async def error_handler(update: object, context: CallbackContext):
        logger.warning(f"Ошибка: {context.error}")

    app.add_error_handler(error_handler)

    print("Бот запущен!")
    app.run_polling()





