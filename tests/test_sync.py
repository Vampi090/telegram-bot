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
from handlers.sync import (
    sync_menu_handler,
    sync_handler,
    export_callback_handler,
    handle_sync_menu_callback,
    handle_sync_callback,
    handle_export_callback
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
class TestSyncHandlerPatterns(unittest.TestCase):
    def test_sync_menu_handler_pattern(self):
        self.assertEqual(sync_menu_handler.pattern.pattern, '^sync_export')

    def test_sync_handler_pattern(self):
        self.assertEqual(sync_handler.pattern.pattern, '^sync$')

    def test_export_callback_handler_pattern(self):
        self.assertEqual(export_callback_handler.pattern.pattern, '^export$')

@test_category(TestCategory.HANDLERS)
class TestSyncHandlers(unittest.TestCase):
    @patch('handlers.sync.log_command_usage')
    @patch('handlers.sync.sync_menu_keyboard')
    async def test_sync_menu_callback(self, mock_keyboard, mock_log):
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
        await handle_sync_menu_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that sync_menu_keyboard was called
        mock_keyboard.assert_called_once()
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once_with(
            text="📥 Меню синхронізації та експорту",
            reply_markup="keyboard"
        )

    @patch('handlers.sync.log_command_usage')
    @patch('handlers.sync.sync_with_google_sheets')
    @patch('handlers.sync.sync_menu_keyboard')
    async def test_sync_callback(self, mock_keyboard, mock_sync, mock_log):
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
        
        context.bot.send_message = MagicMock(return_value=asyncio.Future())
        context.bot.send_message.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the sync_with_google_sheets mock
        mock_sync.return_value = (True, "Sync successful")
        
        # Configure the keyboard mock
        mock_keyboard.return_value = "keyboard"
        
        # Call the handler
        await handle_sync_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that sync_with_google_sheets was called with the correct user_id
        mock_sync.assert_called_once_with(123)
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once_with(
            text="🔄 Синхронізація даних запущена...",
            reply_markup=None
        )
        
        # Check that context.bot.send_message was called with the correct parameters
        context.bot.send_message.assert_called_once_with(
            chat_id=123,
            text="Sync successful",
            reply_markup="keyboard"
        )

    @patch('handlers.sync.log_command_usage')
    @patch('handlers.sync.export_transactions_to_excel')
    @patch('handlers.sync.sync_menu_keyboard')
    @patch('handlers.sync.open')
    @patch('handlers.sync.os.remove')
    async def test_export_callback_success(self, mock_remove, mock_open, mock_keyboard, mock_export, mock_log):
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
        
        context.bot.send_document = MagicMock(return_value=asyncio.Future())
        context.bot.send_document.return_value.set_result(None)
        context.bot.send_message = MagicMock(return_value=asyncio.Future())
        context.bot.send_message.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the export_transactions_to_excel mock
        mock_export.return_value = "export.xlsx"
        
        # Configure the keyboard mock
        mock_keyboard.return_value = "keyboard"
        
        # Configure the open mock
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the handler
        await handle_export_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that export_transactions_to_excel was called with the correct user_id
        mock_export.assert_called_once_with(123)
        
        # Check that callback_query.answer was called
        update.callback_query.answer.assert_called_once()
        
        # Check that context.bot.send_document and context.bot.send_message were called
        context.bot.send_document.assert_called_once()
        context.bot.send_message.assert_called_once_with(
            chat_id=123,
            text="📁 Експорт даних в Excel завершено.",
            reply_markup="keyboard"
        )
        
        # Check that os.remove was called with the correct file path
        mock_remove.assert_called_once_with("export.xlsx")

    @patch('handlers.sync.log_command_usage')
    @patch('handlers.sync.export_transactions_to_excel')
    @patch('handlers.sync.sync_menu_keyboard')
    async def test_export_callback_no_data(self, mock_keyboard, mock_export, mock_log):
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
        
        # Configure the export_transactions_to_excel mock
        mock_export.return_value = None
        
        # Configure the keyboard mock
        mock_keyboard.return_value = "keyboard"
        
        # Call the handler
        await handle_export_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that export_transactions_to_excel was called with the correct user_id
        mock_export.assert_called_once_with(123)
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once_with(
            text="❌ У вас немає даних для експорту.",
            reply_markup="keyboard"
        )

if __name__ == '__main__':
    unittest.main()