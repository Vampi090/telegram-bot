from telegram import Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext


async def send_or_edit_menu(
        update: Update,
        context: CallbackContext,
        text: str,
        reply_markup: InlineKeyboardMarkup,
        parse_mode: str = None
):
    if 'menu_message_id' not in context.user_data:
        context.user_data['menu_message_id'] = None

    chat_id = update.effective_chat.id

    if update.callback_query:
        await update.callback_query.answer()

        callback_message_id = update.callback_query.message.message_id

        message = await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )

        context.user_data['menu_message_id'] = callback_message_id

        return message

    if context.user_data['menu_message_id']:
        try:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=context.user_data['menu_message_id']
            )
        except Exception:
            pass

    message = await update.message.reply_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode
    )

    context.user_data['menu_message_id'] = message.message_id

    return message
