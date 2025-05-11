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
from handlers.reminders import (
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
    handle_reminder_callback,
    handle_create_reminder,
    handle_list_reminders,
    handle_view_reminder,
    handle_edit_reminder,
    handle_complete_reminder,
    handle_delete_reminder,
    handle_delete_reminder_confirm,
    check_and_send_reminders
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
class TestRemindersHandlerPatterns(unittest.TestCase):
    def test_reminder_handler_pattern(self):
        self.assertEqual(reminder_handler.pattern.pattern, '^reminders$')

    def test_list_reminders_handler_pattern(self):
        self.assertEqual(list_reminders_handler.pattern.pattern, '^list_reminders$')

    def test_view_reminder_handler_pattern(self):
        self.assertEqual(view_reminder_handler.pattern.pattern, '^view_reminder_')

    def test_edit_reminder_handler_pattern(self):
        self.assertEqual(edit_reminder_handler.pattern.pattern, '^edit_reminder_')

    def test_complete_reminder_handler_pattern(self):
        self.assertEqual(complete_reminder_handler.pattern.pattern, '^complete_reminder_')

    def test_delete_reminder_handler_pattern(self):
        self.assertEqual(delete_reminder_handler.pattern.pattern, '^delete_reminder_')

    def test_delete_reminder_confirm_handler_pattern(self):
        self.assertEqual(delete_reminder_confirm_handler.pattern.pattern, '^delete_reminder_confirm_')

    def test_create_reminder_conversation_entry_points(self):
        entry_points = create_reminder_conversation.entry_points
        self.assertEqual(len(entry_points), 1)
        self.assertEqual(entry_points[0].pattern.pattern, '^create_reminder$')

    def test_edit_reminder_title_conversation_entry_points(self):
        entry_points = edit_reminder_title_conversation.entry_points
        self.assertEqual(len(entry_points), 1)
        self.assertEqual(entry_points[0].pattern.pattern, '^edit_reminder_title_')

    def test_edit_reminder_datetime_conversation_entry_points(self):
        entry_points = edit_reminder_datetime_conversation.entry_points
        self.assertEqual(len(entry_points), 1)
        self.assertEqual(entry_points[0].pattern.pattern, '^edit_reminder_datetime_')

@test_category(TestCategory.HANDLERS)
class TestRemindersHandlers(unittest.TestCase):
    @patch('handlers.reminders.log_command_usage')
    @patch('handlers.reminders.reminder_menu_keyboard')
    async def test_reminder_callback(self, mock_keyboard, mock_log):
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
        await handle_reminder_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that reminder_menu_keyboard was called
        mock_keyboard.assert_called_once()
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()

    @patch('handlers.reminders.log_command_usage')
    async def test_create_reminder(self, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.edit_message_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.edit_message_text.return_value.set_result(None)
        
        context.user_data = {}
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Call the handler
        result = await handle_create_reminder(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that context.user_data was updated
        self.assertEqual(context.user_data["reminder_state"], "waiting_for_title")
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        
        # Check that the correct state was returned
        from handlers.reminders import ConversationHandler
        self.assertEqual(result, "waiting_for_title")

    @patch('handlers.reminders.log_command_usage')
    @patch('handlers.reminders.get_reminders')
    async def test_list_reminders_no_reminders(self, mock_get_reminders, mock_log):
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
        
        # Configure the get_reminders mock
        mock_get_reminders.return_value = []
        
        # Call the handler
        await handle_list_reminders(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that get_reminders was called with the correct user_id
        mock_get_reminders.assert_called_once_with(123)
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        
        # Check that the message contains the expected text
        args, kwargs = update.callback_query.edit_message_text.call_args
        self.assertTrue("У вас немає активних нагадувань" in args[0])

    @patch('handlers.reminders.log_command_usage')
    @patch('handlers.reminders.get_reminders')
    async def test_list_reminders_with_reminders(self, mock_get_reminders, mock_log):
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
        
        # Configure the get_reminders mock
        mock_get_reminders.return_value = [
            (1, "Buy milk", "2023-12-31 12:00:00", 0, "2023-01-01 12:00:00"),
            (2, "Pay bills", "2023-12-31 15:00:00", 0, "2023-01-01 15:00:00")
        ]
        
        # Call the handler
        await handle_list_reminders(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that get_reminders was called with the correct user_id
        mock_get_reminders.assert_called_once_with(123)
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        
        # Check that the message contains the expected text
        args, kwargs = update.callback_query.edit_message_text.call_args
        self.assertTrue("Ваші нагадування" in args[0])
        self.assertTrue("Buy milk" in args[0])
        self.assertTrue("Pay bills" in args[0])

    @patch('handlers.reminders.log_command_usage')
    @patch('handlers.reminders.get_reminder')
    async def test_view_reminder(self, mock_get_reminder, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.data = "view_reminder_1"
        update.callback_query.from_user.id = 123
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.edit_message_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.edit_message_text.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the get_reminder mock
        mock_get_reminder.return_value = (1, "Buy milk", "2023-12-31 12:00:00", 0, "2023-01-01 12:00:00")
        
        # Call the handler
        await handle_view_reminder(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that get_reminder was called with the correct user_id and reminder_id
        mock_get_reminder.assert_called_once_with(123, 1)
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        
        # Check that the message contains the expected text
        args, kwargs = update.callback_query.edit_message_text.call_args
        self.assertTrue("Buy milk" in args[0])
        self.assertTrue("2023-12-31 12:00:00" in args[0])

    @patch('handlers.reminders.log_command_usage')
    @patch('handlers.reminders.get_reminder')
    async def test_edit_reminder(self, mock_get_reminder, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.data = "edit_reminder_1"
        update.callback_query.from_user.id = 123
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.edit_message_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.edit_message_text.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the get_reminder mock
        mock_get_reminder.return_value = (1, "Buy milk", "2023-12-31 12:00:00", 0, "2023-01-01 12:00:00")
        
        # Call the handler
        await handle_edit_reminder(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that get_reminder was called with the correct user_id and reminder_id
        mock_get_reminder.assert_called_once_with(123, 1)
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        
        # Check that the message contains the expected text
        args, kwargs = update.callback_query.edit_message_text.call_args
        self.assertTrue("Редагування нагадування" in args[0])
        self.assertTrue("Buy milk" in args[0])

    @patch('handlers.reminders.log_command_usage')
    @patch('handlers.reminders.get_reminder')
    @patch('handlers.reminders.mark_reminder_completed')
    async def test_complete_reminder(self, mock_mark_completed, mock_get_reminder, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.data = "complete_reminder_1"
        update.callback_query.from_user.id = 123
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.edit_message_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.edit_message_text.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the get_reminder mock
        mock_get_reminder.return_value = (1, "Buy milk", "2023-12-31 12:00:00", 0, "2023-01-01 12:00:00")
        
        # Configure the mark_reminder_completed mock
        mock_mark_completed.return_value = True
        
        # Call the handler
        await handle_complete_reminder(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that get_reminder was called with the correct user_id and reminder_id
        mock_get_reminder.assert_called_once_with(123, 1)
        
        # Check that mark_reminder_completed was called with the correct user_id and reminder_id
        mock_mark_completed.assert_called_once_with(123, 1)
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        
        # Check that the message contains the expected text
        args, kwargs = update.callback_query.edit_message_text.call_args
        self.assertTrue("✅ Нагадування виконано" in args[0])
        self.assertTrue("Buy milk" in args[0])

    @patch('handlers.reminders.log_command_usage')
    @patch('handlers.reminders.get_reminder')
    async def test_delete_reminder(self, mock_get_reminder, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.data = "delete_reminder_1"
        update.callback_query.from_user.id = 123
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.edit_message_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.edit_message_text.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the get_reminder mock
        mock_get_reminder.return_value = (1, "Buy milk", "2023-12-31 12:00:00", 0, "2023-01-01 12:00:00")
        
        # Call the handler
        await handle_delete_reminder(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that get_reminder was called with the correct user_id and reminder_id
        mock_get_reminder.assert_called_once_with(123, 1)
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        
        # Check that the message contains the expected text
        args, kwargs = update.callback_query.edit_message_text.call_args
        self.assertTrue("❓ Ви впевнені, що хочете видалити нагадування" in args[0])
        self.assertTrue("Buy milk" in args[0])

    @patch('handlers.reminders.log_command_usage')
    @patch('handlers.reminders.delete_reminder')
    async def test_delete_reminder_confirm(self, mock_delete_reminder, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.data = "delete_reminder_confirm_1"
        update.callback_query.from_user.id = 123
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.edit_message_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.edit_message_text.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the delete_reminder mock
        mock_delete_reminder.return_value = True
        
        # Call the handler
        await handle_delete_reminder_confirm(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that delete_reminder was called with the correct user_id and reminder_id
        mock_delete_reminder.assert_called_once_with(123, 1)
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        
        # Check that the message contains the expected text
        args, kwargs = update.callback_query.edit_message_text.call_args
        self.assertTrue("✅ Нагадування видалено" in args[0])

if __name__ == '__main__':
    unittest.main()