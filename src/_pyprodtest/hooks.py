"""
Pytest plugin hooks for capturing test results and artifacts.
"""
import logging

from _pyprodtest.test_record import TestRecord

_observers = []
messages = []

class ListHandler(logging.Handler):
    """
    Temp logging handler to capture log messages in a list.
    """
    def emit(self, record):
        messages.append(self.format(record))

def pytest_configure():
    """
    Hook to configure our settings
    """

    logging.debug("Pyprodtest observers setup: %s", _observers)

    handler = ListHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Pyprodtest configuration complete.")

def pytest_report_collectionfinish(items):
    """
    Hook to execute when test collection is finished.
    """
    test_records = []

    for item in items:
        test_metadata = getattr(item.function, "test_meta", {})
        test_name = test_metadata.get("name", item.nodeid)
        test_desc = test_metadata.get("desc", "")
        test_reqs = test_metadata.get("requirements", [])
        test_steps = test_metadata.get("steps", [])

        test_record = TestRecord(
            name=test_name,
            description=test_desc,
            requirements=test_reqs,
            steps=test_steps
        )

        test_records.append(test_record)

    logging.debug("Collected test records: %s", test_records)


def pytest_runtest_setup(item):
    """
    Hook to execute before each test setup.
    """
    
    logging.debug(item.nodeid)

def pytest_runtest_call(item):
    """
    Hook to execute before each test call.
    """
    # Custom logic before test execution
    logging.debug("Called")

def pytest_runtest_teardown(item, nextitem):
    """
    Hook to execute after each test teardown.
    """
    # Custom logic after test teardown
    pass

def pytest_runtest_logreport(report):
    """
    Hook to execute when a test report is generated.
    """
    pass

def pytest_terminal_summary(terminalreporter, config):
    """
    Hook to add a summary to the terminal report.
    """
    terminalreporter.write_sep("=", "Custom Summary")
    for message in messages:
        terminalreporter.write_line(message)