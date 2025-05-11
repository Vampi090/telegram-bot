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
from keyboards.main_menu import main_menu_keyboard
from handlers.transactions import handle_transactions_callback
from handlers.analytics import analytics_handler
from handlers.budget import budgeting_handler
from handlers.tools import tools_handler
from handlers.sync import sync_menu_handler
from handlers.debt import debt_handler
from handlers.help import help_section_handler

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
        UI = "User Interface"

# Apply the test_category decorator to the test class
@test_category(TestCategory.UI)
class TestMainMenuButtons(unittest.TestCase):
    def test_main_menu_keyboard_structure(self):
        keyboard = main_menu_keyboard()

        # Check that the keyboard has 7 rows (one for each button)
        self.assertEqual(len(keyboard.inline_keyboard), 7)

        # Check each button's text and callback_data
        expected_buttons = [
            ("📥 Транзакції", "transactions"),
            ("📊 Аналітика та звіти", "analytics"),
            ("🎯 Цілі та бюджет", "budgeting"),
            ("💼 Фінансові інструменти", "tools"),
            ("🔄 Синхронізація та експорт", "sync_export"),
            ("🤝 Облік боргів", "debt"),
            ("❓ Допомога", "help_section")
        ]

        for i, (expected_text, expected_callback) in enumerate(expected_buttons):
            button = keyboard.inline_keyboard[i][0]
            self.assertEqual(button.text, expected_text)
            self.assertEqual(button.callback_data, expected_callback)

    @patch('handlers.transactions.log_command_usage')
    @patch('handlers.transactions.send_or_edit_menu')
    async def test_transactions_handler(self, mock_send_or_edit, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        update.effective_user = MagicMock()

        # Configure the mocks to return awaitable objects
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)

        mock_send_or_edit.return_value = asyncio.Future()
        mock_send_or_edit.return_value.set_result(None)

        # Call the handler
        await handle_transactions_callback(update, context)

        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)

        # Check that send_or_edit_menu was called with the correct parameters
        mock_send_or_edit.assert_called_once()
        args, kwargs = mock_send_or_edit.call_args
        self.assertEqual(args[0], update)
        self.assertEqual(args[1], context)
        self.assertEqual(args[2], "📥 Меню керування транзакціями")

    def test_analytics_handler_pattern(self):
        self.assertEqual(analytics_handler.pattern.pattern, '^analytics$')

    def test_budgeting_handler_pattern(self):
        self.assertEqual(budgeting_handler.pattern.pattern, '^budgeting$')

    def test_tools_handler_pattern(self):
        self.assertEqual(tools_handler.pattern.pattern, '^tools')

    def test_sync_menu_handler_pattern(self):
        self.assertEqual(sync_menu_handler.pattern.pattern, '^sync_export')

    def test_debt_handler_pattern(self):
        self.assertEqual(debt_handler.pattern.pattern, '^debt$')

    def test_help_section_handler_pattern(self):
        self.assertEqual(help_section_handler.pattern.pattern, '^help_section$')

if __name__ == '__main__':
    unittest.main()
