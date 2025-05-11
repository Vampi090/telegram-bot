import logging
from services.database_service import init_database
from handlers import register_handlers
from handlers.reminders import check_and_send_reminders
from telegram.ext import Application
from config import TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="bot.log"
)
logger = logging.getLogger(__name__)

app = Application.builder().token(TOKEN).build()


def main():
    logger.info("Запуск Telegram-бота...")

    init_database()

    register_handlers(app)

    job_queue = app.job_queue
    job_queue.run_repeating(check_and_send_reminders, interval=60, first=10)
    logger.info("Планувальник нагадувань запущено")

    app.run_polling()


if __name__ == "__main__":
    main()
