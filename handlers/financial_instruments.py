from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
import requests
from services.logging_service import log_command_usage

WAITING_FOR_AMOUNT = 1
WAITING_FOR_FROM_CURRENCY = 2
WAITING_FOR_TO_CURRENCY = 3


async def handle_convert_callback(update: Update, context: CallbackContext):
    await log_command_usage(update, context)
    context.user_data.clear()

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "💱 Конвертація валют\n\n"
        "Введіть суму для конвертації:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="tools")]
        ])
    )
    return WAITING_FOR_AMOUNT


async def handle_amount_input(update: Update, context: CallbackContext):
    try:
        amount = float(update.message.text)
        context.user_data['amount'] = amount

        await update.message.reply_text(
            f"Сума: {amount}\n"
            "Введіть вихідну валюту (наприклад, USD):",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("USD", callback_data="from_USD"),
                 InlineKeyboardButton("EUR", callback_data="from_EUR"),
                 InlineKeyboardButton("UAH", callback_data="from_UAH")],
                [InlineKeyboardButton("🔙 Назад", callback_data="convert")]
            ])
        )
        return WAITING_FOR_FROM_CURRENCY

    except ValueError:
        await update.message.reply_text(
            "❌ Невірний формат числа. Будь ласка, введіть число:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="tools")]
            ])
        )
        return WAITING_FOR_AMOUNT


async def handle_from_currency_input(update: Update, context: CallbackContext):
    if update.callback_query:
        query = update.callback_query
        await query.answer()

        from_currency = query.data.split("_")[1]
        context.user_data['from_currency'] = from_currency

        await query.edit_message_text(
            f"Сума: {context.user_data['amount']}\n"
            f"З: {from_currency}\n"
            "Введіть цільову валюту (наприклад, EUR):",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("USD", callback_data="to_USD"),
                 InlineKeyboardButton("EUR", callback_data="to_EUR"),
                 InlineKeyboardButton("UAH", callback_data="to_UAH")],
                [InlineKeyboardButton("🔙 Назад", callback_data="convert")]
            ])
        )
    else:
        from_currency = update.message.text.upper()
        context.user_data['from_currency'] = from_currency

        await update.message.reply_text(
            f"Сума: {context.user_data['amount']}\n"
            f"З: {from_currency}\n"
            "Введіть цільову валюту (наприклад, EUR):",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("USD", callback_data="to_USD"),
                 InlineKeyboardButton("EUR", callback_data="to_EUR"),
                 InlineKeyboardButton("UAH", callback_data="to_UAH")],
                [InlineKeyboardButton("🔙 Назад", callback_data="convert")]
            ])
        )
    return WAITING_FOR_TO_CURRENCY


async def handle_to_currency_input(update: Update, context: CallbackContext):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        to_currency = query.data.split("_")[1]
    else:
        to_currency = update.message.text.upper()

    amount = context.user_data['amount']
    from_currency = context.user_data['from_currency']

    rate = await get_exchange_rate(from_currency, to_currency)

    if rate is None:
        result_text = f"❌ Не вдалося отримати курс для {from_currency} → {to_currency}."
    else:
        converted_amount = round(amount * rate, 2)
        result_text = f"💱 {amount} {from_currency} ≈ {converted_amount} {to_currency}"

    if update.callback_query:
        await update.callback_query.edit_message_text(
            result_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Нова конвертація", callback_data="convert")],
                [InlineKeyboardButton("🔙 Назад до інструментів", callback_data="tools")]
            ])
        )
    else:
        await update.message.reply_text(
            result_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Нова конвертація", callback_data="convert")],
                [InlineKeyboardButton("🔙 Назад до інструментів", callback_data="tools")]
            ])
        )

    return ConversationHandler.END


async def get_exchange_rate(from_currency, to_currency):
    url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        rates = data.get("rates", {})
        rate = rates.get(to_currency)

        if rate is None:
            print(f"[Курс валют] ❌ Не знайдено курс: {from_currency} → {to_currency}")
            return None

        print(f"[Курс валют] 💱 Курс {from_currency} → {to_currency} = {rate}")
        return rate

    except requests.exceptions.Timeout:
        print("[Курс валют] ⏱ Таймаут при отриманні курсу.")
    except requests.exceptions.RequestException as e:
        print(f"[Курс валют] ⚠️ Помилка запиту: {e}")

    return None


async def cancel_conversion(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "💱 Конвертація скасована.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад до інструментів", callback_data="tools")]
        ])
    )
    return ConversationHandler.END


currency_conversion_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_convert_callback, pattern="^convert$")],
    states={
        WAITING_FOR_AMOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_input),
            CallbackQueryHandler(cancel_conversion, pattern="^tools$"),
            CallbackQueryHandler(handle_convert_callback, pattern="^convert$")
        ],
        WAITING_FOR_FROM_CURRENCY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_from_currency_input),
            CallbackQueryHandler(handle_from_currency_input, pattern="^from_"),
            CallbackQueryHandler(handle_convert_callback, pattern="^convert$")
        ],
        WAITING_FOR_TO_CURRENCY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_to_currency_input),
            CallbackQueryHandler(handle_to_currency_input, pattern="^to_"),
            CallbackQueryHandler(handle_convert_callback, pattern="^convert$")
        ]
    },
    fallbacks=[
        CallbackQueryHandler(cancel_conversion, pattern="^tools$"),
        CallbackQueryHandler(handle_convert_callback, pattern="^convert$")
    ],
    allow_reentry=True
)
