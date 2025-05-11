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
from handlers.analytics import handle_analytics_callback
from handlers.budget import handle_budgeting_callback
from handlers.tools import handle_tools_callback
from handlers.sync import handle_sync_menu_callback
from handlers.debt import handle_debt_callback
from handlers.help import handle_help_callback

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

# Apply the test_category decorator to the test class
@test_category(TestCategory.HANDLERS)
class TestMainMenuHandlers(unittest.TestCase):
    @patch('handlers.analytics.log_command_usage')
    async def test_analytics_handler(self, mock_log):
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

        # Call the handler
        await handle_analytics_callback(update, context)

        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)

        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()

    @patch('handlers.budget.log_command_usage')
    @patch('handlers.budget.send_or_edit_menu')
    async def test_budgeting_handler(self, mock_send_or_edit, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()

        # Configure the mocks to return awaitable objects
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)

        mock_send_or_edit.return_value = asyncio.Future()
        mock_send_or_edit.return_value.set_result(None)

        # Call the handler
        await handle_budgeting_callback(update, context)

        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)

        # Check that send_or_edit_menu was called
        mock_send_or_edit.assert_called_once()
        args, kwargs = mock_send_or_edit.call_args
        self.assertEqual(args[0], update)
        self.assertEqual(args[1], context)

    @patch('handlers.tools.log_command_usage')
    async def test_tools_handler(self, mock_log):
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

        # Call the handler
        await handle_tools_callback(update, context)

        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)

        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()

    @patch('handlers.sync.log_command_usage')
    async def test_sync_menu_handler(self, mock_log):
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

        # Call the handler
        await handle_sync_menu_callback(update, context)

        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)

        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()

    @patch('handlers.debt.log_command_usage')
    async def test_debt_handler(self, mock_log):
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

        # Call the handler
        await handle_debt_callback(update, context)

        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)

        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()

    @patch('handlers.help.log_command_usage')
    async def test_help_section_handler(self, mock_log):
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

        # Call the handler
        await handle_help_callback(update, context)

        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)

        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()

if __name__ == '__main__':
    unittest.main()
