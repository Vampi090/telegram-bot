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
    track_goals_handler,
    piggy_bank_handler,
    piggy_bank_view_handler,
    piggy_bank_delete_handler,
    piggy_bank_delete_confirm_handler,
    piggy_bank_create_conversation,
    piggy_bank_add_funds_conversation
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
    debt_category_handler,
    debt_action_handler,
    debt_message_handler,
    adddebt_handler,
    set_reminder_handler,
    add_debt_conv_handler,
    debt_reminder_handler,
    debt_reminder_conv_handler
)
from .help import help_section_handler, guide_handler
from .reminders import (
    reminder_handler,
    list_reminders_handler,
    view_reminder_handler,
    edit_reminder_handler,
    complete_reminder_handler,
    delete_reminder_handler,
    delete_reminder_confirm_handler,
    create_reminder_conversation,
    edit_reminder_title_conversation,
    edit_reminder_datetime_conversation,
    check_and_send_reminders
)

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

    # Копилка
    app.add_handler(piggy_bank_handler)
    app.add_handler(piggy_bank_view_handler)
    app.add_handler(piggy_bank_delete_handler)
    app.add_handler(piggy_bank_delete_confirm_handler)
    app.add_handler(piggy_bank_create_conversation)
    app.add_handler(piggy_bank_add_funds_conversation)

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
    app.add_handler(debt_category_handler)  # Обработчик категорий долгов (я должен/мне должны)
    app.add_handler(debt_action_handler)  # Обработчик действий с долгами (погашение, удаление)
    app.add_handler(debt_reminder_handler)  # Обработчик напоминаний о долгах
    app.add_handler(debt_reminder_conv_handler)  # Обработчик выбора даты и времени для напоминаний о долгах
    app.add_handler(adddebt_handler)
    app.add_handler(set_reminder_handler)
    app.add_handler(add_debt_conv_handler)

    # Напоминания
    app.add_handler(reminder_handler)
    app.add_handler(list_reminders_handler)
    app.add_handler(view_reminder_handler)
    app.add_handler(edit_reminder_handler)
    app.add_handler(complete_reminder_handler)
    app.add_handler(delete_reminder_handler)
    app.add_handler(delete_reminder_confirm_handler)
    app.add_handler(create_reminder_conversation)
    app.add_handler(edit_reminder_title_conversation)
    app.add_handler(edit_reminder_datetime_conversation)

    # Должен быть последним, чтобы не перехватывать другие сообщения
    app.add_handler(debt_message_handler)

    # Помощь
    app.add_handler(help_section_handler)
    app.add_handler(guide_handler)
