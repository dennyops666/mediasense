"""测试用例装饰器工具。"""

import functools
import re
from typing import Dict, List, Optional

# 全局变量存储测试用例信息
TEST_CASES: Dict[str, Dict] = {}

def parse_docstring(docstring: str) -> Dict:
    """解析测试用例文档字符串。"""
    if not docstring:
        return {}
    
    # 清理文档字符串
    docstring = docstring.strip()
    
    # 初始化结果
    result = {
        'description': '',
        'preconditions': [],
        'steps': [],
        'expected_results': []
    }
    
    # 解析各个部分
    current_section = 'description'
    lines = docstring.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('前置条件：'):
            current_section = 'preconditions'
            continue
        elif line.startswith('步骤：'):
            current_section = 'steps'
            continue
        elif line.startswith('预期：'):
            current_section = 'expected_results'
            continue
            
        if current_section == 'description':
            if line.startswith('测试用例：'):
                result['description'] = line.replace('测试用例：', '').strip()
            else:
                result['description'] = line
        elif current_section == 'preconditions':
            if line.startswith('- '):
                result['preconditions'].append(line[2:])
        elif current_section == 'steps':
            if re.match(r'^\d+\.', line):
                result['steps'].append(line)
        elif current_section == 'expected_results':
            result['expected_results'].append(line)
            
    return result

def test_case(id: str, priority: str, module: str):
    """
    测试用例装饰器。
    
    Args:
        id: 测试用例ID
        priority: 优先级（P0-P3）
        module: 所属模块
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 解析测试用例文档
            doc_info = parse_docstring(func.__doc__)
            
            # 存储测试用例信息
            TEST_CASES[id] = {
                'id': id,
                'name': doc_info.get('description', func.__name__),
                'priority': priority,
                'module': module,
                'function': func.__name__,
                'preconditions': doc_info.get('preconditions', []),
                'steps': doc_info.get('steps', []),
                'expected_results': doc_info.get('expected_results', []),
                'status': 'Not Started'
            }
            
            try:
                # 执行测试用例
                result = func(*args, **kwargs)
                TEST_CASES[id]['status'] = 'Completed'
                return result
            except Exception as e:
                TEST_CASES[id]['status'] = 'Failed'
                TEST_CASES[id]['error'] = str(e)
                raise
                
        return wrapper
    return decorator

def get_test_cases(
    priority: Optional[str] = None,
    module: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict]:
    """
    获取测试用例信息。
    
    Args:
        priority: 按优先级筛选
        module: 按模块筛选
        status: 按状态筛选
    
    Returns:
        符合条件的测试用例列表
    """
    filtered_cases = []
    
    for case in TEST_CASES.values():
        if priority and case['priority'] != priority:
            continue
        if module and case['module'] != module:
            continue
        if status and case['status'] != status:
            continue
        filtered_cases.append(case)
    
    return filtered_cases 