# Засіб запуску тестів Telegram Bot

Цей каталог містить тести для проєкту Telegram Bot. Засіб запуску тестів забезпечує стилізований вивід з категоризацією тестів.

## Запуск тестів

Щоб запустити всі тести, виконайте наступну команду з кореневого каталогу проєкту:

```bash
python tests/run_tests.py
```

Засіб запуску тестів автоматично виявить і запустить усі тестові файли в каталозі tests, які відповідають шаблону імені `test_*.py`. Вам не потрібно змінювати засіб запуску при додаванні нових тестових файлів.

## Категорії тестів

Тести організовані за категоріями для кращої організації та звітності. Доступні категорії:

- **Інтерфейс користувача (UI)**: Тести для компонентів інтерфейсу, таких як клавіатури та меню
- **Обробники повідомлень**: Тести для обробників повідомлень та зворотних викликів
- **Інтеграційні тести**: Тести, які перевіряють спільну роботу кількох компонентів
- **Модульні тести**: Тести для окремих функцій та методів
- **Некатегоризовані тести**: Тести, які не підходять до інших категорій

## Створення нових тестів

### Базова структура

При створенні нових тестових файлів, дотримуйтесь наступних кроків:

1. Назвіть ваш файл з префіксом `test_` (наприклад, `test_my_feature.py`)
2. Імпортуйте необхідні модулі
3. Додайте батьківський каталог до шляху Python
4. Імпортуйте модулі, які ви хочете тестувати
5. Створіть тестові класи, які успадковують `unittest.TestCase`
6. Використовуйте декоратор `@test_category` для категоризації ваших тестів

### Приклад тестового файлу

Ось повний приклад нового тестового файлу:

```python
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

# Import the modules you want to test
from keyboards.main_menu import main_menu_keyboard

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
        UNIT = "Unit Tests"

# Apply the test_category decorator to the test class
@test_category(TestCategory.UNIT)
class TestMyFeature(unittest.TestCase):
    def test_something_synchronous(self):
        # Synchronous test code
        self.assertEqual(1 + 1, 2)

    @patch('module.some_function')
    async def test_something_asynchronous(self, mock_function):
        # Asynchronous test code
        mock_function.return_value = asyncio.Future()
        mock_function.return_value.set_result("mocked result")

        # Test your async code here
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
```

### Використання декоратора

При створенні нових тестових класів, ви можете вказати категорію за допомогою декоратора `@test_category`:

```python
# Import the test_category decorator
from run_tests import test_category, TestCategory

# Apply the test_category decorator to the test class
@test_category(TestCategory.UI)
class MyUITests(unittest.TestCase):
    def test_something(self):
        # Test code here
        pass
```

Якщо ви запускаєте тестовий файл безпосередньо (не через run_tests.py), вам слід обробити імпорт таким чином:

```python
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
```

## Створення власних категорій

Ви можете створювати власні категорії, додаючи їх до класу `TestCategory` у файлі `run_tests.py`:

```python
class TestCategory:
    UI = "User Interface"
    HANDLERS = "Message Handlers"
    INTEGRATION = "Integration Tests"
    UNIT = "Unit Tests"
    UNCATEGORIZED = "Uncategorized Tests"
    # Add your custom category here
    MY_CATEGORY = "My Custom Category"
```

Потім використовуйте її з декоратором:

```python
@test_category(TestCategory.MY_CATEGORY)
class MyCustomCategoryTests(unittest.TestCase):
    # Test methods here
    pass
```

## Вивід тестів

Засіб запуску тестів забезпечує стилізований вивід з:

- Кольоровим кодуванням результатів тестів (зелений для успішних, червоний для невдалих/помилок, жовтий для пропущених)
- Чіткими символами для статусу тесту (✓, ✗, ⚠, ⚪)
- Групуванням тестів за категоріями
- Підсумковою статистикою за категоріями та загалом
- Інформацією про час виконання

Приклад виводу:

```
TELEGRAM BOT TEST RUNNER
Started at: 2023-11-15 12:34:56
================================================================================

Running tests for category: User Interface

Running standard tests for TestMainMenuButtons:
  ✓ test_main_menu_keyboard_structure
  ✓ test_analytics_handler_pattern
  ✓ test_budgeting_handler_pattern
  ✓ test_debt_handler_pattern
  ✓ test_help_section_handler_pattern
  ✓ test_sync_menu_handler_pattern
  ✓ test_tools_handler_pattern

Running async tests for TestMainMenuButtons:
Running async test: TestMainMenuButtons.test_transactions_handler
  ✓ test_transactions_handler

Running tests for category: Message Handlers

Running async tests for TestMainMenuHandlers:
Running async test: TestMainMenuHandlers.test_analytics_handler
  ✓ test_analytics_handler
Running async test: TestMainMenuHandlers.test_budgeting_handler
  ✓ test_budgeting_handler
Running async test: TestMainMenuHandlers.test_debt_handler
  ✓ test_debt_handler
Running async test: TestMainMenuHandlers.test_help_section_handler
  ✓ test_help_section_handler
Running async test: TestMainMenuHandlers.test_sync_menu_handler
  ✓ test_sync_menu_handler
Running async test: TestMainMenuHandlers.test_tools_handler
  ✓ test_tools_handler

================================================================================
TEST SUMMARY
================================================================================

Category: User Interface
  Total: 8
  Passed: 8

Category: Message Handlers
  Total: 6
  Passed: 6

--------------------------------------------------------------------------------
OVERALL RESULTS:
  Total tests: 14
  Passed: 14

Time elapsed: 0.12 seconds
================================================================================
```
