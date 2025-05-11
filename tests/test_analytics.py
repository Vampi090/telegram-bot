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
from handlers.analytics import (
    analytics_handler,
    stats_handler,
    chart_handler,
    report_handler,
    export_handler,
    handle_analytics_callback,
    handle_stats_callback,
    handle_chart_callback,
    handle_report_callback,
    handle_export_command
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
class TestAnalyticsHandlerPatterns(unittest.TestCase):
    def test_analytics_handler_pattern(self):
        self.assertEqual(analytics_handler.pattern.pattern, '^analytics$')

    def test_stats_handler_pattern(self):
        self.assertEqual(stats_handler.pattern.pattern, '^stats$')

    def test_chart_handler_pattern(self):
        self.assertEqual(chart_handler.pattern.pattern, '^chart$')

    def test_report_handler_pattern(self):
        self.assertEqual(report_handler.pattern.pattern, '^report$')

    def test_export_handler_command(self):
        self.assertEqual(export_handler.command, 'export')

@test_category(TestCategory.HANDLERS)
class TestAnalyticsHandlers(unittest.TestCase):
    @patch('handlers.analytics.log_command_usage')
    @patch('handlers.analytics.analytics_menu_keyboard')
    async def test_analytics_callback(self, mock_keyboard, mock_log):
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
        await handle_analytics_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once_with(
            text="📥 Меню аналітики",
            reply_markup="keyboard"
        )

    @patch('handlers.analytics.log_command_usage')
    @patch('handlers.analytics.get_expense_stats')
    @patch('handlers.analytics.analytics_menu_keyboard')
    async def test_stats_callback(self, mock_keyboard, mock_get_stats, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.from_user.id = 123
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.edit_message_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.edit_message_text.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the get_expense_stats mock
        mock_get_stats.return_value = [("Food", 100), ("Transport", 50)]
        
        # Configure the keyboard mock
        mock_keyboard.return_value = "keyboard"
        
        # Call the handler
        await handle_stats_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that get_expense_stats was called with the correct user_id
        mock_get_stats.assert_called_once_with(123)
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()

    @patch('handlers.analytics.log_command_usage')
    @patch('handlers.analytics.generate_expense_chart')
    @patch('handlers.analytics.analytics_menu_keyboard')
    @patch('handlers.analytics.open')
    @patch('handlers.analytics.os.remove')
    async def test_chart_callback(self, mock_remove, mock_open, mock_keyboard, mock_generate_chart, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.from_user.id = 123
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.edit_message_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.edit_message_text.return_value.set_result(None)
        
        context.bot.send_photo = MagicMock(return_value=asyncio.Future())
        context.bot.send_photo.return_value.set_result(None)
        context.bot.send_message = MagicMock(return_value=asyncio.Future())
        context.bot.send_message.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the generate_expense_chart mock
        mock_generate_chart.return_value = "chart.png"
        
        # Configure the keyboard mock
        mock_keyboard.return_value = "keyboard"
        
        # Configure the open mock
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the handler
        await handle_chart_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that generate_expense_chart was called with the correct user_id
        mock_generate_chart.assert_called_once_with(123)
        
        # Check that callback_query.answer was called
        update.callback_query.answer.assert_called_once()
        
        # Check that context.bot.send_photo and context.bot.send_message were called
        context.bot.send_photo.assert_called_once()
        context.bot.send_message.assert_called_once()
        
        # Check that os.remove was called with the correct file path
        mock_remove.assert_called_once_with("chart.png")

    @patch('handlers.analytics.log_command_usage')
    @patch('handlers.analytics.get_transaction_report')
    @patch('handlers.analytics.analytics_menu_keyboard')
    async def test_report_callback(self, mock_keyboard, mock_get_report, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.from_user.id = 123
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.edit_message_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.edit_message_text.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the get_transaction_report mock
        mock_get_report.return_value = {
            'days': 30,
            'total_income': 1000,
            'total_expense': 500,
            'balance': 500,
            'top_expense_categories': [('Food', 300), ('Transport', 200)],
            'transaction_count': 10
        }
        
        # Configure the keyboard mock
        mock_keyboard.return_value = "keyboard"
        
        # Call the handler
        await handle_report_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that get_transaction_report was called with the correct user_id and days
        mock_get_report.assert_called_once_with(123, days=30)
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()

    @patch('handlers.analytics.log_command_usage')
    @patch('handlers.analytics.export_transactions_to_excel')
    @patch('handlers.analytics.open')
    @patch('handlers.analytics.os.remove')
    async def test_export_command(self, mock_remove, mock_open, mock_export, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks
        update.effective_user.id = 123
        update.message.reply_text = MagicMock(return_value=asyncio.Future())
        update.message.reply_text.return_value.set_result(None)
        
        context.bot.send_document = MagicMock(return_value=asyncio.Future())
        context.bot.send_document.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the export_transactions_to_excel mock
        mock_export.return_value = "export.xlsx"
        
        # Configure the open mock
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the handler
        await handle_export_command(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that export_transactions_to_excel was called with the correct user_id
        mock_export.assert_called_once_with(123)
        
        # Check that context.bot.send_document was called
        context.bot.send_document.assert_called_once()
        
        # Check that os.remove was called with the correct file path
        mock_remove.assert_called_once_with("export.xlsx")

if __name__ == '__main__':
    unittest.main()