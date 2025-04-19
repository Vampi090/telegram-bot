from telegram import Update
from telegram.ext import CallbackContext
import logging

logger = logging.getLogger(__name__)


async def log_command_usage(update: Update, context: CallbackContext):
    user = update.effective_user
    message = update.message or update.callback_query

    user_info = f"User({user.id}, {user.first_name}, {user.last_name}, {user.username})"
    command = message.text if message else "callback_query"
    logger.info(f"Command executed: {command} by {user_info}")
