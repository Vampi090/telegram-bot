import logging
from telegram import Update
from telegram.ext import CallbackContext
from datetime import datetime
from services.database_service import create_command_logs_table, insert_command_log

logger = logging.getLogger(__name__)

create_command_logs_table()


async def log_command_usage(update: Update, context: CallbackContext):
    """Логує використання команди та записує подію в базу даних."""
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

    insert_command_log(user_id, username, full_name, command, timestamp)

    logger.info(f"Команда {command} була викликана користувачем {user_id} ({username})")
