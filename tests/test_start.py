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
from handlers.start import (
    start_handler,
    start
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
class TestStartHandlerPatterns(unittest.TestCase):
    def test_start_handler_command(self):
        self.assertEqual(start_handler.command, 'start')

@test_category(TestCategory.HANDLERS)
class TestStartHandlers(unittest.TestCase):
    @patch('handlers.start.log_command_usage')
    @patch('handlers.start.main_menu_keyboard')
    @patch('handlers.start.send_or_edit_menu')
    async def test_start_handler(self, mock_send_or_edit, mock_keyboard, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks
        update.effective_user = MagicMock()
        update.effective_user.first_name = "Test User"
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the keyboard mock
        mock_keyboard.return_value = "keyboard"
        
        # Configure the send_or_edit_menu mock
        mock_send_or_edit.return_value = asyncio.Future()
        mock_send_or_edit.return_value.set_result(None)
        
        # Call the handler
        await start(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that main_menu_keyboard was called
        mock_keyboard.assert_called_once()
        
        # Check that send_or_edit_menu was called with the correct parameters
        mock_send_or_edit.assert_called_once()
        args, kwargs = mock_send_or_edit.call_args
        self.assertEqual(args[0], update)
        self.assertEqual(args[1], context)
        self.assertTrue("👋 Привіт, Test User!" in args[2])
        self.assertEqual(args[3], "keyboard")

if __name__ == '__main__':
    unittest.main()