from django.test.runner import DiscoverRunner

class NoDbTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        """Override the database creation"""
        pass

    def teardown_databases(self, old_config, **kwargs):
        """Override the database teardown"""
        pass 