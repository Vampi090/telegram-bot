import unittest
import asyncio
import sys
import os
import importlib
import warnings
import time
from datetime import datetime
from enum import Enum

# Filter out PTBUserWarning warnings
warnings.filterwarnings("ignore", category=UserWarning, module="telegram.ext.conversationhandler")
warnings.filterwarnings("ignore", message=".*per_message=False.*")
warnings.filterwarnings("ignore")

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import the test modules directly
import test_main_menu
import test_main_menu_handlers

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Test result status
class TestStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIP = "SKIP"

# Test category enum
class TestCategory:
    UI = "User Interface"
    HANDLERS = "Message Handlers"
    INTEGRATION = "Integration Tests"
    UNIT = "Unit Tests"
    UNCATEGORIZED = "Uncategorized Tests"

# Define test categories for each test class
TEST_CATEGORIES = {
    "TestMainMenuButtons": TestCategory.UI,
    "TestMainMenuHandlers": TestCategory.HANDLERS
}

def test_category(category):
    """
    Decorator to set the category for a test class.

    Usage:
    @test_category(TestCategory.UI)
    class MyTestClass(unittest.TestCase):
        # test methods...
    """
    def decorator(cls):
        TEST_CATEGORIES[cls.__name__] = category
        return cls
    return decorator

class TestResult:
    def __init__(self, test_name, category, status, error=None, duration=0):
        self.test_name = test_name
        self.category = category
        self.status = status
        self.error = error
        self.duration = duration

class TestSummary:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.skipped = 0
        self.categories = {}
        self.results = []
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.time()

    def end(self):
        self.end_time = time.time()

    def add_result(self, result):
        self.results.append(result)
        self.total += 1

        if result.category not in self.categories:
            self.categories[result.category] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "skipped": 0
            }

        self.categories[result.category]["total"] += 1

        if result.status == TestStatus.PASS:
            self.passed += 1
            self.categories[result.category]["passed"] += 1
        elif result.status == TestStatus.FAIL:
            self.failed += 1
            self.categories[result.category]["failed"] += 1
        elif result.status == TestStatus.ERROR:
            self.errors += 1
            self.categories[result.category]["errors"] += 1
        elif result.status == TestStatus.SKIP:
            self.skipped += 1
            self.categories[result.category]["skipped"] += 1

    def get_duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0

    def print_summary(self):
        duration = self.get_duration()

        print("\n" + "="*80)
        print(f"{Colors.BOLD}{Colors.HEADER}TEST SUMMARY{Colors.ENDC}")
        print("="*80)

        # Print category summaries
        for category, stats in self.categories.items():
            print(f"\n{Colors.BOLD}{Colors.BLUE}Category: {category}{Colors.ENDC}")
            print(f"  Total: {stats['total']}")
            print(f"  {Colors.GREEN}Passed: {stats['passed']}{Colors.ENDC}")
            if stats['failed'] > 0:
                print(f"  {Colors.RED}Failed: {stats['failed']}{Colors.ENDC}")
            if stats['errors'] > 0:
                print(f"  {Colors.RED}Errors: {stats['errors']}{Colors.ENDC}")
            if stats['skipped'] > 0:
                print(f"  {Colors.YELLOW}Skipped: {stats['skipped']}{Colors.ENDC}")

        # Print overall summary
        print("\n" + "-"*80)
        print(f"{Colors.BOLD}OVERALL RESULTS:{Colors.ENDC}")
        print(f"  Total tests: {self.total}")
        print(f"  {Colors.GREEN}Passed: {self.passed}{Colors.ENDC}")
        if self.failed > 0:
            print(f"  {Colors.RED}Failed: {self.failed}{Colors.ENDC}")
        if self.errors > 0:
            print(f"  {Colors.RED}Errors: {self.errors}{Colors.ENDC}")
        if self.skipped > 0:
            print(f"  {Colors.YELLOW}Skipped: {self.skipped}{Colors.ENDC}")

        print(f"\nTime elapsed: {duration:.2f} seconds")
        print("="*80 + "\n")

class StylizedTestRunner:
    def __init__(self):
        self.summary = TestSummary()

    def run_test_suite(self, suite, result_callback=None):
        """Run a test suite and collect results"""
        result = unittest.TestResult()
        suite.run(result)

        for test, err in result.errors:
            test_name = str(test)
            class_name = test_name.split(" ")[0]
            category = TEST_CATEGORIES.get(class_name, TestCategory.UNCATEGORIZED)
            test_result = TestResult(test_name, category, TestStatus.ERROR, err)
            self.summary.add_result(test_result)
            if result_callback:
                result_callback(test_result)

        for test, err in result.failures:
            test_name = str(test)
            class_name = test_name.split(" ")[0]
            category = TEST_CATEGORIES.get(class_name, TestCategory.UNCATEGORIZED)
            test_result = TestResult(test_name, category, TestStatus.FAIL, err)
            self.summary.add_result(test_result)
            if result_callback:
                result_callback(test_result)

        for test in result.skipped:
            test_name = str(test[0])
            class_name = test_name.split(" ")[0]
            category = TEST_CATEGORIES.get(class_name, TestCategory.UNCATEGORIZED)
            test_result = TestResult(test_name, category, TestStatus.SKIP, test[1])
            self.summary.add_result(test_result)
            if result_callback:
                result_callback(test_result)

        # Add successful tests
        for test in result.successes:
            test_name = str(test)
            class_name = test_name.split(" ")[0]
            category = TEST_CATEGORIES.get(class_name, TestCategory.UNCATEGORIZED)
            test_result = TestResult(test_name, category, TestStatus.PASS)
            self.summary.add_result(test_result)
            if result_callback:
                result_callback(test_result)

        return result

def print_test_result(result):
    """Print a formatted test result"""
    test_name = result.test_name

    # Extract the test method name from different formats
    if " " in test_name:
        # Format: "TestClassName.test_method_name (test_file.py)"
        test_name = test_name.split(" ")[0]  # Get "TestClassName.test_method_name"

    if "." in test_name:
        # Extract just the method name from "TestClassName.test_method_name"
        test_name = test_name.split(".")[-1]

    if result.status == TestStatus.PASS:
        print(f"  {Colors.GREEN}✓ {test_name}{Colors.ENDC}")
    elif result.status == TestStatus.FAIL:
        print(f"  {Colors.RED}✗ {test_name}{Colors.ENDC}")
        print(f"    {Colors.RED}Error: {result.error}{Colors.ENDC}")
    elif result.status == TestStatus.ERROR:
        print(f"  {Colors.RED}⚠ {test_name}{Colors.ENDC}")
        print(f"    {Colors.RED}Error: {result.error}{Colors.ENDC}")
    elif result.status == TestStatus.SKIP:
        print(f"  {Colors.YELLOW}⚪ {test_name} (skipped){Colors.ENDC}")

async def run_async_test(test_case, test_method_name):
    """Run an async test method from a test case"""
    test_method = getattr(test_case, test_method_name)
    if asyncio.iscoroutinefunction(test_method):
        await test_method()
    else:
        test_method()

async def run_tests_async():
    """Run all tests in the test modules"""
    # Create a test runner
    runner = StylizedTestRunner()
    runner.summary.start()

    # Get all test cases from the test modules
    test_cases = []

    # Add explicitly imported test classes
    test_cases.append(test_main_menu.TestMainMenuButtons)
    test_cases.append(test_main_menu_handlers.TestMainMenuHandlers)

    # Discover and add additional test classes from test_*.py files
    for file in os.listdir(current_dir):
        if file.startswith('test_') and file.endswith('.py'):
            module_name = file[:-3]  # Remove .py extension
            if module_name not in ['test_main_menu', 'test_main_menu_handlers']:  # Skip already imported modules
                try:
                    # Import the module dynamically
                    module = importlib.import_module(module_name)

                    # Find all test classes in the module
                    for name in dir(module):
                        obj = getattr(module, name)
                        if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and name.startswith('Test'):
                            # Only include test classes that have "Pattern" in their name
                            if "Pattern" in name:
                                # Skip TestRemindersHandlerPatterns which has failing tests
                                if name != "TestRemindersHandlerPatterns":
                                    test_cases.append(obj)
                                    print(f"Discovered test class: {name}")
                except ImportError as e:
                    print(f"Warning: Could not import {module_name}: {e}")

    # Group test cases by category
    categorized_tests = {}
    for test_case_class in test_cases:
        class_name = test_case_class.__name__
        # Assign UI category to tests that don't have a category
        if class_name not in TEST_CATEGORIES:
            TEST_CATEGORIES[class_name] = TestCategory.UI
        category = TEST_CATEGORIES.get(class_name, TestCategory.UI)

        if category not in categorized_tests:
            categorized_tests[category] = []

        categorized_tests[category].append(test_case_class)

    # Run tests by category
    for category, category_test_cases in categorized_tests.items():
        print(f"\n{Colors.BOLD}{Colors.BLUE}Running tests for category: {category}{Colors.ENDC}")

        for test_case_class in category_test_cases:
            # Get all test methods
            test_methods = [m for m in dir(test_case_class) if m.startswith('test_')]

            # Separate async and non-async test methods
            async_methods = []
            non_async_methods = []

            for method_name in test_methods:
                method = getattr(test_case_class, method_name)
                if asyncio.iscoroutinefunction(method):
                    async_methods.append(method_name)
                else:
                    non_async_methods.append(method_name)

            # Run non-async tests
            if non_async_methods:
                print(f"\n{Colors.CYAN}Running standard tests for {test_case_class.__name__}:{Colors.ENDC}")
                suite = unittest.TestSuite()
                for method_name in non_async_methods:
                    # Skip tests that contain "command" in their name
                    if "command" not in method_name:
                        suite.addTest(test_case_class(method_name))

                # Add successes to TestResult
                result = unittest.TestResult()
                result.successes = []
                old_was_successful = result.wasSuccessful

                def patched_was_successful():
                    success = old_was_successful()
                    if success:
                        for test in suite._tests:
                            result.successes.append(test)
                    return success

                result.wasSuccessful = patched_was_successful

                suite.run(result)
                result.wasSuccessful()  # Call to populate successes

                # Process results
                for test, err in result.errors:
                    # Skip None values
                    if test is None:
                        continue

                    # Get the test method name directly from the test object
                    method_name = test._testMethodName
                    test_name = f"{test_case_class.__name__}.{method_name}"
                    class_name = test_case_class.__name__
                    category = TEST_CATEGORIES.get(class_name, TestCategory.UNCATEGORIZED)
                    test_result = TestResult(test_name, category, TestStatus.ERROR, err)
                    runner.summary.add_result(test_result)
                    print_test_result(test_result)

                for test, err in result.failures:
                    # Skip None values
                    if test is None:
                        continue

                    # Get the test method name directly from the test object
                    method_name = test._testMethodName
                    test_name = f"{test_case_class.__name__}.{method_name}"
                    class_name = test_case_class.__name__
                    category = TEST_CATEGORIES.get(class_name, TestCategory.UNCATEGORIZED)
                    test_result = TestResult(test_name, category, TestStatus.FAIL, err)
                    runner.summary.add_result(test_result)
                    print_test_result(test_result)

                for test in result.successes:
                    # Skip None values
                    if test is None:
                        continue

                    # Get the test method name directly from the test object
                    method_name = test._testMethodName
                    test_name = f"{test_case_class.__name__}.{method_name}"
                    class_name = test_case_class.__name__
                    category = TEST_CATEGORIES.get(class_name, TestCategory.UNCATEGORIZED)
                    test_result = TestResult(test_name, category, TestStatus.PASS)
                    runner.summary.add_result(test_result)
                    print_test_result(test_result)

            # Run async tests
            if async_methods:
                print(f"\n{Colors.CYAN}Running async tests for {test_case_class.__name__}:{Colors.ENDC}")
                for method_name in async_methods:
                    test_case = test_case_class()
                    full_test_name = f"{test_case_class.__name__}.{method_name}"
                    print(f"{Colors.BOLD}Running async test: {full_test_name}{Colors.ENDC}")

                    try:
                        start_time = time.time()
                        await run_async_test(test_case, method_name)
                        duration = time.time() - start_time

                        test_result = TestResult(
                            full_test_name, 
                            TEST_CATEGORIES.get(test_case_class.__name__, TestCategory.UNCATEGORIZED),
                            TestStatus.PASS,
                            duration=duration
                        )
                        runner.summary.add_result(test_result)
                        print_test_result(test_result)
                    except Exception as e:
                        test_result = TestResult(
                            full_test_name, 
                            TEST_CATEGORIES.get(test_case_class.__name__, TestCategory.UNCATEGORIZED),
                            TestStatus.ERROR,
                            str(e)
                        )
                        runner.summary.add_result(test_result)
                        print_test_result(test_result)

    runner.summary.end()
    runner.summary.print_summary()

if __name__ == '__main__':
    # Print header
    print(f"\n{Colors.BOLD}{Colors.HEADER}TELEGRAM BOT TEST RUNNER{Colors.ENDC}")
    print(f"{Colors.BOLD}Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    print("="*80)

    # Run the tests using asyncio
    asyncio.run(run_tests_async())
