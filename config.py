import logging
import sys

# Telegram Token
TOKEN = "7888156941:AAGeuOWwEYSZwjOv1aY5eKUcPMxJlTPANuk"

# Состояния ConversationHandler
WAITING_FOR_AMOUNT = 1
WAITING_FOR_NAME = ""
DEBT_NAME, DEBT_AMOUNT = range(2)

# Типы данных
AMOUNT, CATEGORY, TYPE = range(3)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,  # Уровень логирования (INFO - выводить основные события)
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),  # Лог в файл bot.log с указанием кодировки
        logging.StreamHandler(sys.stdout)  # Лог в консоль с кодировкой utf-8
    ]
)
logger = logging.getLogger(__name__)

# job_queue (если используется и нужен глобально)
job_queue = None

# Экспорт доступных переменных в другие модули
__all__ = [
    "TOKEN",
    "WAITING_FOR_AMOUNT",
    "WAITING_FOR_NAME",
    "DEBT_NAME",
    "DEBT_AMOUNT",
    "AMOUNT",
    "CATEGORY",
    "TYPE",
    "logger",
    "job_queue",
]
