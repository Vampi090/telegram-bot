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
from handlers.transactions import (
    transactions_handler,
    add_transaction_handler,
    history_handler,
    history_callback_handler,
    filter_transactions_handler,
    undo_callback_handler,
    add_transaction_conv_handler,
    handle_transactions_callback,
    add_transaction,
    handle_add_callback,
    handle_amount_input,
    handle_category_input,
    history,
    filter_transactions,
    undo_transaction
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
class TestTransactionsHandlerPatterns(unittest.TestCase):
    def test_transactions_handler_pattern(self):
        self.assertEqual(transactions_handler.pattern.pattern, '^transactions$')

    def test_add_transaction_handler_command(self):
        self.assertEqual(add_transaction_handler.command, 'add')

    def test_history_handler_command(self):
        self.assertEqual(history_handler.command, 'history')

    def test_history_callback_handler_pattern(self):
        self.assertEqual(history_callback_handler.pattern.pattern, '^history$')

    def test_filter_transactions_handler_command(self):
        self.assertEqual(filter_transactions_handler.command, 'transactions')

    def test_undo_callback_handler_pattern(self):
        self.assertEqual(undo_callback_handler.pattern.pattern, '^undo$')

    def test_add_transaction_conv_handler_entry_points(self):
        entry_points = add_transaction_conv_handler.entry_points
        self.assertEqual(len(entry_points), 1)
        self.assertEqual(entry_points[0].pattern.pattern, '^add$')

@test_category(TestCategory.HANDLERS)
class TestTransactionsHandlers(unittest.TestCase):
    @patch('handlers.transactions.log_command_usage')
    @patch('handlers.transactions.transaction_menu_keyboard')
    @patch('handlers.transactions.send_or_edit_menu')
    async def test_transactions_callback(self, mock_send_or_edit, mock_keyboard, mock_log):
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
        await handle_transactions_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that transaction_menu_keyboard was called
        mock_keyboard.assert_called_once()
        
        # Check that send_or_edit_menu was called with the correct parameters
        mock_send_or_edit.assert_called_once_with(update, context, "📥 Меню керування транзакціями", "keyboard")

    @patch('handlers.transactions.log_command_usage')
    @patch('handlers.transactions.add_new_transaction')
    @patch('handlers.transactions.send_or_edit_menu')
    async def test_add_transaction_success(self, mock_send_or_edit, mock_add_transaction, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks
        update.message = MagicMock()
        update.effective_user.id = 123
        context.args = ["100", "food"]
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the add_new_transaction mock
        mock_transaction = MagicMock()
        mock_transaction.amount = 100
        mock_transaction.category = "food"
        mock_transaction.transaction_type = "income"
        mock_add_transaction.return_value = mock_transaction
        
        # Configure the send_or_edit_menu mock
        mock_send_or_edit.return_value = asyncio.Future()
        mock_send_or_edit.return_value.set_result(None)
        
        # Call the handler
        await add_transaction(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that add_new_transaction was called with the correct parameters
        mock_add_transaction.assert_called_once_with(123, 100.0, "food")
        
        # Check that send_or_edit_menu was called with the correct parameters
        mock_send_or_edit.assert_called_once()
        args, kwargs = mock_send_or_edit.call_args
        self.assertEqual(args[0], update)
        self.assertEqual(args[1], context)
        self.assertTrue("✅ Транзакция добавлена" in args[2])

    @patch('handlers.transactions.log_command_usage')
    @patch('handlers.transactions.send_or_edit_menu')
    async def test_add_transaction_no_args(self, mock_send_or_edit, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks
        update.message = MagicMock()
        context.args = []
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the send_or_edit_menu mock
        mock_send_or_edit.return_value = asyncio.Future()
        mock_send_or_edit.return_value.set_result(None)
        
        # Call the handler
        await add_transaction(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that send_or_edit_menu was called with the correct parameters
        mock_send_or_edit.assert_called_once()
        args, kwargs = mock_send_or_edit.call_args
        self.assertEqual(args[0], update)
        self.assertEqual(args[1], context)
        self.assertTrue("⚠️ Неверный формат" in args[2])

    @patch('handlers.transactions.log_command_usage')
    @patch('handlers.transactions.send_or_edit_menu')
    async def test_handle_add_callback(self, mock_send_or_edit, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks to return awaitable objects
        update.callback_query = MagicMock()
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the send_or_edit_menu mock
        mock_send_or_edit.return_value = asyncio.Future()
        mock_send_or_edit.return_value.set_result(None)
        
        # Call the handler
        result = await handle_add_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that send_or_edit_menu was called with the correct parameters
        mock_send_or_edit.assert_called_once()
        args, kwargs = mock_send_or_edit.call_args
        self.assertEqual(args[0], update)
        self.assertEqual(args[1], context)
        self.assertTrue("✍️ *Введите сумму:*" in args[2])
        
        # Check that the correct state was returned
        from handlers.transactions import WAITING_FOR_AMOUNT
        self.assertEqual(result, WAITING_FOR_AMOUNT)

    @patch('handlers.transactions.log_command_usage')
    @patch('handlers.transactions.get_user_transaction_history')
    @patch('handlers.transactions.send_or_edit_menu')
    async def test_history_no_transactions(self, mock_send_or_edit, mock_get_history, mock_log):
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
        
        # Configure the get_user_transaction_history mock
        mock_get_history.return_value = []
        
        # Configure the send_or_edit_menu mock
        mock_send_or_edit.return_value = asyncio.Future()
        mock_send_or_edit.return_value.set_result(None)
        
        # Call the handler
        await history(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that get_user_transaction_history was called with the correct parameters
        mock_get_history.assert_called_once_with(123, limit=10)
        
        # Check that send_or_edit_menu was called with the correct parameters
        mock_send_or_edit.assert_called_once()
        args, kwargs = mock_send_or_edit.call_args
        self.assertEqual(args[0], update)
        self.assertEqual(args[1], context)
        self.assertTrue("📜 У вас еще нет транзакций" in args[2])

    @patch('handlers.transactions.log_command_usage')
    @patch('handlers.transactions.filter_user_transactions')
    @patch('handlers.transactions.send_or_edit_menu')
    async def test_filter_transactions_success(self, mock_send_or_edit, mock_filter, mock_log):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks
        update.message.from_user.id = 123
        context.args = ["food"]
        
        # Configure the log_command_usage mock to return an awaitable
        mock_log.return_value = asyncio.Future()
        mock_log.return_value.set_result(None)
        
        # Configure the filter_user_transactions mock
        mock_transaction = MagicMock()
        mock_transaction.timestamp = "2023-01-01"
        mock_transaction.amount = 100
        mock_transaction.category = "food"
        mock_transaction.transaction_type = "income"
        mock_filter.return_value = [mock_transaction]
        
        # Configure the send_or_edit_menu mock
        mock_send_or_edit.return_value = asyncio.Future()
        mock_send_or_edit.return_value.set_result(None)
        
        # Call the handler
        await filter_transactions(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that filter_user_transactions was called with the correct parameters
        mock_filter.assert_called_once_with(123, "food")
        
        # Check that send_or_edit_menu was called with the correct parameters
        mock_send_or_edit.assert_called_once()
        args, kwargs = mock_send_or_edit.call_args
        self.assertEqual(args[0], update)
        self.assertEqual(args[1], context)
        self.assertTrue("📂 *Транзакции по фильтру:*" in args[2])

    @patch('handlers.transactions.log_command_usage')
    @patch('handlers.transactions.get_user_last_transaction')
    @patch('handlers.transactions.delete_user_transaction')
    @patch('handlers.transactions.send_or_edit_menu')
    async def test_undo_transaction_success(self, mock_send_or_edit, mock_delete, mock_get_last, mock_log):
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
        
        # Configure the get_user_last_transaction mock
        mock_transaction = MagicMock()
        mock_transaction.id = 1
        mock_transaction.timestamp = "2023-01-01"
        mock_transaction.amount = 100
        mock_transaction.category = "food"
        mock_transaction.transaction_type = "income"
        mock_get_last.return_value = mock_transaction
        
        # Configure the delete_user_transaction mock
        mock_delete.return_value = True
        
        # Configure the send_or_edit_menu mock
        mock_send_or_edit.return_value = asyncio.Future()
        mock_send_or_edit.return_value.set_result(None)
        
        # Call the handler
        await undo_transaction(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that get_user_last_transaction was called with the correct parameters
        mock_get_last.assert_called_once_with(123)
        
        # Check that delete_user_transaction was called with the correct parameters
        mock_delete.assert_called_once_with(1)
        
        # Check that send_or_edit_menu was called with the correct parameters
        mock_send_or_edit.assert_called_once()
        args, kwargs = mock_send_or_edit.call_args
        self.assertEqual(args[0], update)
        self.assertEqual(args[1], context)
        self.assertTrue("✅ Последняя транзакция отменена" in args[2])

if __name__ == '__main__':
    unittest.main()