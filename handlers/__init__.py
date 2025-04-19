from .start import start_handler
from .main_menu import back_to_main_menu_handler
from .transactions import transactions_handler
from .analytics import analytics_handler
from .budget import budgeting_handler
from .tools import tools_handler
from .sync import sync_menu_handler
from .debt import debt_handler
from .help import help_handler

def register_handlers(app):
    """
    Регистрирует обработчики в приложении Telegram.
    Параметр: app - объект Telegram Application.
    """
    app.add_handler(start_handler)
    app.add_handler(back_to_main_menu_handler)
    app.add_handler(transactions_handler)
    app.add_handler(analytics_handler)
    app.add_handler(budgeting_handler)
    app.add_handler(tools_handler)
    app.add_handler(sync_menu_handler)
    app.add_handler(debt_handler)
    app.add_handler(help_handler)