from .start import start_handler

def register_handlers(app):
    """
    Регистрирует обработчики в приложении Telegram.
    Параметр: app - объект Telegram Application.
    """
    app.add_handler(start_handler)  # Регистрация команды /start