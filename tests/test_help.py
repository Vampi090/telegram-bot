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
from handlers.help import (
    help_section_handler,
    guide_handler,
    handle_help_callback,
    handle_guide_callback
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
class TestHelpHandlerPatterns(unittest.TestCase):
    def test_help_section_handler_pattern(self):
        self.assertEqual(help_section_handler.pattern.pattern, '^help_section$')

    def test_guide_handler_pattern(self):
        self.assertEqual(guide_handler.pattern.pattern, '^guide$')

@test_category(TestCategory.HANDLERS)
class TestHelpHandlers(unittest.TestCase):
    @patch('handlers.help.log_command_usage')
    @patch('handlers.help.help_menu_keyboard')
    async def test_help_callback(self, mock_keyboard, mock_log):
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
        await handle_help_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that help_menu_keyboard was called
        mock_keyboard.assert_called_once()
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once_with(
            text="❓ Допомога та інструкції",
            reply_markup="keyboard"
        )

    @patch('handlers.help.log_command_usage')
    @patch('handlers.help.help_menu_keyboard')
    async def test_guide_callback(self, mock_keyboard, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.edit_message_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.edit_message_text.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the keyboard mock
        mock_keyboard.return_value = "keyboard"
        
        # Call the handler
        await handle_guide_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that help_menu_keyboard was called
        mock_keyboard.assert_called_once()
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        
        # Check that the guide text was included in the message
        args, kwargs = update.callback_query.edit_message_text.call_args
        self.assertTrue("📖 <b>Повний посібник з використання бота:</b>" in kwargs["text"])
        self.assertEqual(kwargs["parse_mode"], "HTML")
        self.assertEqual(kwargs["reply_markup"], "keyboard")

if __name__ == '__main__':
    unittest.main()