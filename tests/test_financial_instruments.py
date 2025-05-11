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
from handlers.financial_instruments import (
    currency_conversion_handler,
    handle_convert_callback,
    handle_amount_input,
    handle_from_currency_input,
    handle_to_currency_input,
    get_exchange_rate,
    cancel_conversion,
    WAITING_FOR_AMOUNT,
    WAITING_FOR_FROM_CURRENCY,
    WAITING_FOR_TO_CURRENCY
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
class TestFinancialInstrumentsHandlerPatterns(unittest.TestCase):
    def test_currency_conversion_handler_entry_points(self):
        entry_points = currency_conversion_handler.entry_points
        self.assertEqual(len(entry_points), 1)
        self.assertEqual(entry_points[0].pattern.pattern, "^convert$")

    def test_currency_conversion_handler_states(self):
        states = currency_conversion_handler.states
        self.assertIn(WAITING_FOR_AMOUNT, states)
        self.assertIn(WAITING_FOR_FROM_CURRENCY, states)
        self.assertIn(WAITING_FOR_TO_CURRENCY, states)

    def test_currency_conversion_handler_fallbacks(self):
        fallbacks = currency_conversion_handler.fallbacks
        self.assertEqual(len(fallbacks), 2)
        self.assertEqual(fallbacks[0].pattern.pattern, "^tools$")
        self.assertEqual(fallbacks[1].pattern.pattern, "^convert$")

@test_category(TestCategory.HANDLERS)
class TestFinancialInstrumentsHandlers(unittest.TestCase):
    @patch('handlers.financial_instruments.log_command_usage')
    async def test_handle_convert_callback(self, mock_log):
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
        result = await handle_convert_callback(update, context)
        
        # Check that log_command_usage was called
        mock_log.assert_called_once_with(update, context)
        
        # Check that context.user_data was cleared
        self.assertEqual(context.user_data, {})
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        
        # Check that the correct state was returned
        self.assertEqual(result, WAITING_FOR_AMOUNT)

    async def test_handle_amount_input_valid(self):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks
        update.message.text = "100"
        update.message.reply_text = MagicMock(return_value=asyncio.Future())
        update.message.reply_text.return_value.set_result(None)
        
        context.user_data = {}
        
        # Call the handler
        result = await handle_amount_input(update, context)
        
        # Check that context.user_data was updated
        self.assertEqual(context.user_data["amount"], 100.0)
        
        # Check that update.message.reply_text was called
        update.message.reply_text.assert_called_once()
        
        # Check that the correct state was returned
        self.assertEqual(result, WAITING_FOR_FROM_CURRENCY)

    async def test_handle_amount_input_invalid(self):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks
        update.message.text = "invalid"
        update.message.reply_text = MagicMock(return_value=asyncio.Future())
        update.message.reply_text.return_value.set_result(None)
        
        context.user_data = {}
        
        # Call the handler
        result = await handle_amount_input(update, context)
        
        # Check that update.message.reply_text was called with an error message
        update.message.reply_text.assert_called_once()
        args, kwargs = update.message.reply_text.call_args
        self.assertTrue("❌ Невірний формат числа" in args[0])
        
        # Check that the correct state was returned
        self.assertEqual(result, WAITING_FOR_AMOUNT)

    async def test_handle_from_currency_input_callback(self):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks
        update.callback_query = MagicMock()
        update.callback_query.data = "from_USD"
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.edit_message_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.edit_message_text.return_value.set_result(None)
        
        context.user_data = {"amount": 100.0}
        
        # Call the handler
        result = await handle_from_currency_input(update, context)
        
        # Check that context.user_data was updated
        self.assertEqual(context.user_data["from_currency"], "USD")
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        
        # Check that the correct state was returned
        self.assertEqual(result, WAITING_FOR_TO_CURRENCY)

    async def test_handle_from_currency_input_message(self):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks
        update.callback_query = None
        update.message.text = "USD"
        update.message.reply_text = MagicMock(return_value=asyncio.Future())
        update.message.reply_text.return_value.set_result(None)
        
        context.user_data = {"amount": 100.0}
        
        # Call the handler
        result = await handle_from_currency_input(update, context)
        
        # Check that context.user_data was updated
        self.assertEqual(context.user_data["from_currency"], "USD")
        
        # Check that update.message.reply_text was called
        update.message.reply_text.assert_called_once()
        
        # Check that the correct state was returned
        self.assertEqual(result, WAITING_FOR_TO_CURRENCY)

    @patch('handlers.financial_instruments.get_exchange_rate')
    async def test_handle_to_currency_input_callback_success(self, mock_get_rate):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks
        update.callback_query = MagicMock()
        update.callback_query.data = "to_EUR"
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.edit_message_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.edit_message_text.return_value.set_result(None)
        
        context.user_data = {"amount": 100.0, "from_currency": "USD"}
        
        # Configure the get_exchange_rate mock
        mock_get_rate.return_value = asyncio.Future()
        mock_get_rate.return_value.set_result(0.85)
        
        # Call the handler
        result = await handle_to_currency_input(update, context)
        
        # Check that get_exchange_rate was called with the correct parameters
        mock_get_rate.assert_called_once_with("USD", "EUR")
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        
        # Check that the correct state was returned
        from telegram.ext import ConversationHandler
        self.assertEqual(result, ConversationHandler.END)

    @patch('handlers.financial_instruments.get_exchange_rate')
    async def test_handle_to_currency_input_message_success(self, mock_get_rate):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks
        update.callback_query = None
        update.message.text = "EUR"
        update.message.reply_text = MagicMock(return_value=asyncio.Future())
        update.message.reply_text.return_value.set_result(None)
        
        context.user_data = {"amount": 100.0, "from_currency": "USD"}
        
        # Configure the get_exchange_rate mock
        mock_get_rate.return_value = asyncio.Future()
        mock_get_rate.return_value.set_result(0.85)
        
        # Call the handler
        result = await handle_to_currency_input(update, context)
        
        # Check that get_exchange_rate was called with the correct parameters
        mock_get_rate.assert_called_once_with("USD", "EUR")
        
        # Check that update.message.reply_text was called
        update.message.reply_text.assert_called_once()
        
        # Check that the correct state was returned
        from telegram.ext import ConversationHandler
        self.assertEqual(result, ConversationHandler.END)

    @patch('handlers.financial_instruments.get_exchange_rate')
    async def test_handle_to_currency_input_failure(self, mock_get_rate):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks
        update.callback_query = MagicMock()
        update.callback_query.data = "to_XYZ"
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.edit_message_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.edit_message_text.return_value.set_result(None)
        
        context.user_data = {"amount": 100.0, "from_currency": "USD"}
        
        # Configure the get_exchange_rate mock
        mock_get_rate.return_value = asyncio.Future()
        mock_get_rate.return_value.set_result(None)
        
        # Call the handler
        result = await handle_to_currency_input(update, context)
        
        # Check that get_exchange_rate was called with the correct parameters
        mock_get_rate.assert_called_once_with("USD", "XYZ")
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        
        # Check that the correct state was returned
        from telegram.ext import ConversationHandler
        self.assertEqual(result, ConversationHandler.END)

    @patch('handlers.financial_instruments.requests.get')
    async def test_get_exchange_rate_success(self, mock_get):
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "rates": {
                "EUR": 0.85,
                "UAH": 36.5
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Call the function
        rate = await get_exchange_rate("USD", "EUR")
        
        # Check that requests.get was called with the correct URL
        mock_get.assert_called_once_with("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        
        # Check that the correct rate was returned
        self.assertEqual(rate, 0.85)

    @patch('handlers.financial_instruments.requests.get')
    async def test_get_exchange_rate_currency_not_found(self, mock_get):
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "rates": {
                "EUR": 0.85,
                "UAH": 36.5
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Call the function
        rate = await get_exchange_rate("USD", "XYZ")
        
        # Check that requests.get was called with the correct URL
        mock_get.assert_called_once_with("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        
        # Check that None was returned
        self.assertIsNone(rate)

    @patch('handlers.financial_instruments.requests.get')
    async def test_get_exchange_rate_request_exception(self, mock_get):
        # Configure the mock
        mock_get.side_effect = Exception("Test exception")
        
        # Call the function
        rate = await get_exchange_rate("USD", "EUR")
        
        # Check that requests.get was called with the correct URL
        mock_get.assert_called_once_with("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        
        # Check that None was returned
        self.assertIsNone(rate)

    async def test_cancel_conversion(self):
        # Create mock update and context
        update = MagicMock()
        context = MagicMock()
        
        # Configure the mocks
        update.callback_query = MagicMock()
        update.callback_query.answer = MagicMock(return_value=asyncio.Future())
        update.callback_query.answer.return_value.set_result(None)
        update.callback_query.edit_message_text = MagicMock(return_value=asyncio.Future())
        update.callback_query.edit_message_text.return_value.set_result(None)
        
        # Call the handler
        result = await cancel_conversion(update, context)
        
        # Check that callback_query.answer and callback_query.edit_message_text were called
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        
        # Check that the correct state was returned
        from telegram.ext import ConversationHandler
        self.assertEqual(result, ConversationHandler.END)

if __name__ == '__main__':
    unittest.main()