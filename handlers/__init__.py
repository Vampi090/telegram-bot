from .start import start_handler
from .main_menu import back_to_main_menu_handler
from .transactions import (
    transactions_handler, 
    add_transaction_handler, 
    history_handler, 
    history_callback_handler,
    filter_transactions_handler, 
    undo_callback_handler,
    add_transaction_conv_handler
)
from .analytics import (
    analytics_handler,
    stats_handler,
    chart_handler,
    report_handler,
    export_handler
)
from .budget import (
    budgeting_handler,
    goal_handler,
    budget_handler,
    goal_command_handler,
    budget_command_handler,
    track_goals_handler
)
from .tools import tools_handler
from .financial_instruments import currency_conversion_handler
from .sync import (
    sync_menu_handler,
    sync_handler,
    export_callback_handler
)
from .debt import (
    debt_handler,
    debt_command_handler,
    debt_menu_handler,
    debt_message_handler,
    adddebt_handler,
    set_reminder_handler,
    add_debt_conv_handler
)
from .help import help_handler, help_section_handler, guide_handler, help_callback_handler

def register_handlers(app):
    """
    Регистрирует обработчики в приложении Telegram.
    Параметр: app - объект Telegram Application.
    """
    app.add_handler(start_handler)
    app.add_handler(back_to_main_menu_handler)
    app.add_handler(transactions_handler)
    app.add_handler(add_transaction_handler)
    app.add_handler(history_handler)
    app.add_handler(history_callback_handler)
    app.add_handler(filter_transactions_handler)
    app.add_handler(undo_callback_handler)
    app.add_handler(add_transaction_conv_handler)

    # Аналитика
    app.add_handler(analytics_handler)
    app.add_handler(stats_handler)
    app.add_handler(chart_handler)
    app.add_handler(report_handler)
    app.add_handler(export_handler)

    # Бюджет и цели
    app.add_handler(budgeting_handler)
    app.add_handler(goal_handler)
    app.add_handler(budget_handler)
    app.add_handler(goal_command_handler)
    app.add_handler(budget_command_handler)
    app.add_handler(track_goals_handler)

    # Финансовые инструменты
    app.add_handler(tools_handler)
    app.add_handler(currency_conversion_handler)

    # Синхронизация и экспорт
    app.add_handler(sync_menu_handler)
    app.add_handler(sync_handler)
    app.add_handler(export_callback_handler)

    # Долги
    app.add_handler(debt_handler)
    app.add_handler(debt_command_handler)
    app.add_handler(debt_menu_handler)
    app.add_handler(adddebt_handler)
    app.add_handler(set_reminder_handler)
    app.add_handler(add_debt_conv_handler)
    app.add_handler(debt_message_handler)  # Должен быть последним, чтобы не перехватывать другие сообщения

    # Помощь
    app.add_handler(help_section_handler)
    app.add_handler(help_handler)
    app.add_handler(guide_handler)
    app.add_handler(help_callback_handler)
