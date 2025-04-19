import logging
from services.database_service import create_command_logs_table
from handlers import register_handlers
from telegram.ext import Application
from config import TOKEN  # Не забудьте создать файл config.py с вашим токеном

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="bot.log"  # Логи будут сохраняться в файл bot.log
)
logger = logging.getLogger(__name__)

# Инициализация приложения
app = Application.builder().token(TOKEN).build()


def main():
    logger.info("Запуск Telegram-бота...")

    # Создание таблиц в базе данных (если их еще нет)
    create_command_logs_table()

    # Регистрация обработчиков (handlers)
    register_handlers(app)

    # Запуск бота
    app.run_polling()


if __name__ == "__main__":
    main()
