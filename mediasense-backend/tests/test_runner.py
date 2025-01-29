import os
import django
from django.test.runner import DiscoverRunner
import pytest

class PytestTestRunner(DiscoverRunner):
    """使用 pytest 运行测试的测试运行器"""

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """运行测试"""
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediasense.settings.test')
        django.setup()
        
        # 构建 pytest 参数
        pytest_args = []
        
        # 添加测试标签
        if test_labels:
            # 将点号分隔的路径转换为文件路径
            test_paths = []
            for label in test_labels:
                if '.' in label:
                    # 将模块路径转换为文件路径
                    path = label.replace('.', '/')
                    if not path.endswith('.py'):
                        path += '.py'
                    test_paths.append(path)
                else:
                    test_paths.append(label)
            pytest_args.extend(test_paths)
        
        # 添加详细输出
        if self.verbosity > 1:
            pytest_args.append('-v')
        
        # 运行测试
        return pytest.main(pytest_args)

class NoDbTestRunner(DiscoverRunner):
    """使用现有数据库的测试运行器，不创建新的测试数据库"""
    
    def setup_databases(self, **kwargs):
        """覆盖数据库设置方法，直接返回空列表"""
        return []
    
    def teardown_databases(self, old_config, **kwargs):
        """覆盖数据库清理方法，不做任何操作"""
        pass
    
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """运行测试"""
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediasense.settings')
        django.setup()
        
        # 构建 pytest 参数
        pytest_args = []
        
        # 添加测试标签
        if test_labels:
            pytest_args.extend(test_labels)
        
        # 添加详细输出
        if self.verbosity > 1:
            pytest_args.append('-v')
        
        # 添加异步测试支持
        pytest_args.extend(['--asyncio-mode=auto'])
        
        # 运行测试
        return pytest.main(pytest_args) 