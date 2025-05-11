import unittest
import asyncio
import sys
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from handlers.debt import (
    debt_handler,
    debt_command_handler,
    debt_menu_handler,
    debt_category_handler,
    debt_action_handler,
    debt_reminder_handler,
    debt_reminder_conv_handler,
    adddebt_handler,
    set_reminder_handler,
    add_debt_conv_handler,
    handle_debt_callback,
    debt_menu_button_handler,
    debt_type_handler,
    show_debts_by_category,
    handle_debt_reminder_options,
    handle_debt_action,
    adddebt_command
)

# Import the test_category decorator
try:
    from run_tests import test_category, TestCategory
except ImportError:
    # Define dummy decorator for when running tests directly
    def test_category(category):
        def decorator(cls):
            return cls
        return decorator

    class TestCategory:
        HANDLERS = "Message Handlers"
        UI = "User Interface"

# Apply the test_category decorator to the test class
@test_category(TestCategory.UI)
class TestDebtHandlerPatterns(unittest.TestCase):
    def test_debt_handler_pattern(self):
        self.assertEqual(debt_handler.pattern.pattern, '^debt$')

    def test_debt_command_handler_command(self):
        self.assertEqual(debt_command_handler.command, 'debt')

    def test_debt_menu_handler_pattern(self):
        self.assertEqual(debt_menu_handler.pattern.pattern, '^(view_debts|debt_history|close_debt|add_debt|remind_debt|help_debt|debt_back)$')

    def test_debt_category_handler_pattern(self):
        self.assertEqual(debt_category_handler.pattern.pattern, '^(debts_i_owe|debts_owed_to_me)$')

    def test_debt_action_handler_pattern(self):
        self.assertEqual(debt_action_handler.pattern.pattern, '^(pay_debt_|debt_paid_|delete_debt_|confirm_delete_|cancel_delete_)')

    def test_debt_reminder_handler_pattern(self):
        self.assertEqual(debt_reminder_handler.pattern.pattern, '^(debt_reminder_|debt_reminder_option_)')

    def test_adddebt_handler_command(self):
        self.assertEqual(adddebt_handler.command, 'adddebt')

    def test_set_reminder_handler_command(self):
        self.assertEqual(set_reminder_handler.command, 'debtreminder')

@test_category(TestCategory.HANDLERS)
class TestDebtHandlers(unittest.TestCase):
    @patch('handlers.debt.log_command_usage')
    @patch('handlers.debt.debt_menu_keyboard')
    async def test_debt_callback(self, mock_keyboard, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.edit_message_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.edit_message_text.return_value.set_result(None)
        
        update.effective_user = MagicMock()
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the keyboard mock
        mock_keyboard.return_value = "keyboard"
        
        # Call the handler
        await handle_debt_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that debt_menu_keyboard was called
        mock_keyboard.assert_called_once()
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once_with(
            text="🤝 Облік боргів",
            reply_markup="keyboard"
        )

    @patch('handlers.debt.log_command_usage')
    @patch('handlers.debt.get_active_debts')
    async def test_debt_menu_button_handler_view_debts_no_debts(self, mock_get_debts, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.data = "view_debts"
        update.callback_query.from_user.id = 123
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.message.edit_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.message.edit_text.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the get_active_debts mock
        mock_get_debts.return_value = []
        
        # Call the handler
        await debt_menu_button_handler(update, context)
        
        # Check that get_active_debts was called with the correct user_id
        mock_get_debts.assert_called_once_with(123)
        
        # Check that callback_query.message.edit_text was called with the correct parameters
        update.callback_query.message.edit_text.assert_called_once()
        args, kwargs = update.callback_query.message.edit_text.call_args
        self.assertEqual(args[0], "✅ У вас немає боргів.")

    @patch('handlers.debt.log_command_usage')
    @patch('handlers.debt.get_active_debts')
    async def test_debt_menu_button_handler_view_debts_with_debts(self, mock_get_debts, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.data = "view_debts"
        update.callback_query.from_user.id = 123
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.message.edit_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.message.edit_text.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the get_active_debts mock
        mock_get_debts.return_value = [
            ("John", -100, "2023-12-31", "2023-01-01"),  # I owe
            ("Mary", 200, "2023-12-31", "2023-01-01")    # Owed to me
        ]
        
        # Call the handler
        await debt_menu_button_handler(update, context)
        
        # Check that get_active_debts was called with the correct user_id
        mock_get_debts.assert_called_once_with(123)
        
        # Check that callback_query.message.edit_text was called with the correct parameters
        update.callback_query.message.edit_text.assert_called_once()
        args, kwargs = update.callback_query.message.edit_text.call_args
        self.assertTrue("📜 Ваші борги:" in args[0])
        self.assertTrue("💸 Ви винні:" in args[0])
        self.assertTrue("💰 Вам винні:" in args[0])

    @patch('handlers.debt.log_command_usage')
    async def test_debt_type_handler_i_owe(self, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.data = "debt_i_owe"
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.message.edit_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.message.edit_text.return_value.set_result(None)
        
        context.user_data = {}
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Call the handler
        result = await debt_type_handler(update, context)
        
        # Check that callback_query.answer was called
        update.callback_query.answer.assert_called_once()
        
        # Check that context.user_data was updated
        self.assertEqual(context.user_data["debt_type"], "i_owe")
        
        # Check that callback_query.message.edit_text was called with the correct parameters
        update.callback_query.message.edit_text.assert_called_once_with(
            "💸 *Я винен*\n\nВведіть суму боргу:",
            parse_mode="Markdown"
        )
        
        # Check that the correct state was returned
        from handlers.debt import DEBT_AMOUNT_INPUT
        self.assertEqual(result, DEBT_AMOUNT_INPUT)

    @patch('handlers.debt.log_command_usage')
    @patch('handlers.debt.save_debt')
    @patch('handlers.debt.add_new_transaction')
    async def test_adddebt_command_success(self, mock_add_transaction, mock_save_debt, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks
        update.effective_user.id = 123
        update.message.reply_text = MagicMock(return_value=asyncio.Future())
        update.message.reply_text.return_value.set_result(None)
        
        context.args = ["John", "100", "2023-12-31"]
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the save_debt mock
        mock_save_debt.return_value = True
        
        # Call the handler
        await adddebt_command(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that save_debt was called with the correct parameters
        mock_save_debt.assert_called_once_with(123, "John", 100.0, "2023-12-31")
        
        # Check that update.message.reply_text was called with the correct parameters
        update.message.reply_text.assert_called_once()
        args, kwargs = update.message.reply_text.call_args
        self.assertTrue("✅ Борг додано: John — 100.0₴ (до 2023-12-31)" in args[0])

if __name__ == '__main__':
    unittest.main()