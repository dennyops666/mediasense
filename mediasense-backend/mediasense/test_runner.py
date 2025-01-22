import pytest
from django.test.runner import DiscoverRunner

class PytestTestRunner(DiscoverRunner):
    """Runs pytest to discover and run tests."""

    def __init__(self, **kwargs):
        self.pytest_args = []
        super().__init__(**kwargs)

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """Run pytest and return the exitcode.

        Args:
            test_labels: Tests to run.
            extra_tests: Extra tests to run.
            kwargs: Extra arguments.

        Returns:
            Test run exit code.
        """
        self.pytest_args.extend(test_labels)
        return pytest.main(self.pytest_args) 