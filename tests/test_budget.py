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
from handlers.budget import (
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
    handle_budgeting_callback,
    handle_goal_callback,
    handle_budget_callback,
    handle_piggy_bank_callback
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
class TestBudgetHandlerPatterns(unittest.TestCase):
    def test_budgeting_handler_pattern(self):
        self.assertEqual(budgeting_handler.pattern.pattern, '^budgeting$')

    def test_goal_handler_pattern(self):
        self.assertEqual(goal_handler.pattern.pattern, '^goal$')

    def test_budget_handler_pattern(self):
        self.assertEqual(budget_handler.pattern.pattern, '^budget$')

    def test_goal_command_handler_command(self):
        self.assertEqual(goal_command_handler.command, 'goal')

    def test_budget_command_handler_command(self):
        self.assertEqual(budget_command_handler.command, 'budget')

    def test_track_goals_handler_command(self):
        self.assertEqual(track_goals_handler.command, 'track_goals')

    def test_piggy_bank_handler_pattern(self):
        self.assertEqual(piggy_bank_handler.pattern.pattern, '^piggy_bank$')

    def test_piggy_bank_view_handler_pattern(self):
        self.assertEqual(piggy_bank_view_handler.pattern.pattern, '^piggy_bank_view_')

    def test_piggy_bank_delete_handler_pattern(self):
        self.assertEqual(piggy_bank_delete_handler.pattern.pattern, '^piggy_bank_delete_[0-9]+$')

    def test_piggy_bank_delete_confirm_handler_pattern(self):
        self.assertEqual(piggy_bank_delete_confirm_handler.pattern.pattern, '^piggy_bank_delete_confirm_')

@test_category(TestCategory.HANDLERS)
class TestBudgetHandlers(unittest.TestCase):
    @patch('handlers.budget.log_command_usage')
    @patch('handlers.budget.budget_menu_keyboard')
    @patch('handlers.budget.send_or_edit_menu')
    async def test_budgeting_callback(self, mock_send_or_edit, mock_keyboard, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.effective_user = MagicMock()
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the keyboard mock
        mock_keyboard.return_value = "keyboard"
        
        # Configure the send_or_edit_menu mock
        mock_send_or_edit.return_value = asyncio.Future()
        mock_send_or_edit.return_value.set_result(None)
        
        # Call the handler
        await handle_budgeting_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that budget_menu_keyboard was called
        mock_keyboard.assert_called_once()
        
        # Check that send_or_edit_menu was called with the correct parameters
        mock_send_or_edit.assert_called_once_with(update, context, "📥 Меню бюджету", "keyboard")

    @patch('handlers.budget.log_command_usage')
    @patch('handlers.budget.get_goals')
    @patch('handlers.budget.send_or_edit_menu')
    async def test_goal_callback_no_goals(self, mock_send_or_edit, mock_get_goals, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.from_user.id = 123
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the get_goals mock
        mock_get_goals.return_value = []
        
        # Configure the send_or_edit_menu mock
        mock_send_or_edit.return_value = asyncio.Future()
        mock_send_or_edit.return_value.set_result(None)
        
        # Call the handler
        await handle_goal_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that get_goals was called with the correct user_id
        mock_get_goals.assert_called_once_with(123)
        
        # Check that send_or_edit_menu was called with the correct parameters
        mock_send_or_edit.assert_called_once()
        args, kwargs = mock_send_or_edit.call_args
        self.assertEqual(args[0], update)
        self.assertEqual(args[1], context)
        self.assertEqual(args[2], "🎯 У вас поки немає фінансових цілей.")

    @patch('handlers.budget.log_command_usage')
    @patch('handlers.budget.get_goals')
    @patch('handlers.budget.send_or_edit_menu')
    async def test_goal_callback_with_goals(self, mock_send_or_edit, mock_get_goals, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.from_user.id = 123
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the get_goals mock
        mock_get_goals.return_value = [(1000, "Vacation", "2023-12-31")]
        
        # Configure the send_or_edit_menu mock
        mock_send_or_edit.return_value = asyncio.Future()
        mock_send_or_edit.return_value.set_result(None)
        
        # Call the handler
        await handle_goal_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that get_goals was called with the correct user_id
        mock_get_goals.assert_called_once_with(123)
        
        # Check that send_or_edit_menu was called with the correct parameters
        mock_send_or_edit.assert_called_once()
        args, kwargs = mock_send_or_edit.call_args
        self.assertEqual(args[0], update)
        self.assertEqual(args[1], context)
        self.assertTrue("🎯 *Ваші фінансові цілі:*" in args[2])
        self.assertEqual(kwargs["parse_mode"], "Markdown")

    @patch('handlers.budget.log_command_usage')
    @patch('handlers.budget.get_budgets')
    async def test_budget_callback_no_budgets(self, mock_get_budgets, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.from_user.id = 123
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        
        update.effective_chat.id = 123
        
        context.bot.send_message = MagicMock(return_value=asyncio.Future())
        context.bot.send_message.return_value.set_result(MagicMock(message_id=456))
        
        context.user_data = {}
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the get_budgets mock
        mock_get_budgets.return_value = []
        
        # Call the handler
        await handle_budget_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that get_budgets was called with the correct user_id
        mock_get_budgets.assert_called_once_with(123)
        
        # Check that context.bot.send_message was called
        context.bot.send_message.assert_called_once()
        args, kwargs = context.bot.send_message.call_args
        self.assertEqual(kwargs["chat_id"], 123)
        self.assertEqual(kwargs["text"], "💡 У вас поки немає встановленого бюджету.")
        
        # Check that the message_id was stored in context.user_data
        self.assertEqual(context.user_data["budget_message_id"], 456)

    @patch('handlers.budget.log_command_usage')
    @patch('handlers.budget.get_piggy_bank_goals')
    @patch('handlers.budget.send_or_edit_menu')
    async def test_piggy_bank_callback_no_goals(self, mock_send_or_edit, mock_get_goals, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        update.callback_query.from_user.id = 123
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        
        context.user_data = {}
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the get_piggy_bank_goals mock
        mock_get_goals.return_value = []
        
        # Configure the send_or_edit_menu mock
        mock_send_or_edit.return_value = asyncio.Future()
        mock_send_or_edit.return_value.set_result(None)
        
        # Call the handler
        await handle_piggy_bank_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that get_piggy_bank_goals was called with the correct user_id
        mock_get_goals.assert_called_once_with(123)
        
        # Check that send_or_edit_menu was called with the correct parameters
        mock_send_or_edit.assert_called_once()
        args, kwargs = mock_send_or_edit.call_args
        self.assertEqual(args[0], update)
        self.assertEqual(args[1], context)
        self.assertTrue("🐷 *Ваша скарбничка порожня*" in args[2])
        self.assertEqual(kwargs["parse_mode"], "Markdown")

if __name__ == '__main__':
    unittest.main()