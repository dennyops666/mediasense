"""测试文档生成器工具。"""

import os
from datetime import datetime
from typing import Dict, List

from .test_decorators import get_test_cases

def generate_test_plan_md(output_path: str = "docs/backend-test-plan.md"):
    """
    生成测试计划markdown文档。
    
    Args:
        output_path: 输出文件路径
    """
    # 创建输出目录
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 获取所有测试用例
    all_cases = get_test_cases()
    
    # 按优先级和模块组织测试用例
    cases_by_priority: Dict[str, Dict[str, List]] = {
        'P0': {},
        'P1': {},
        'P2': {},
        'P3': {}
    }
    
    for case in all_cases:
        priority = case['priority']
        module = case['module']
        if module not in cases_by_priority[priority]:
            cases_by_priority[priority][module] = []
        cases_by_priority[priority][module].append(case)
    
    # 生成文档内容
    content = [
        "# 后端测试计划",
        "",
        "## 1. 测试概述",
        "",
        "### 1.1 测试目标",
        "- 验证所有后端功能模块的正确性和稳定性",
        "- 确保系统性能满足需求",
        "- 发现并修复潜在的缺陷和安全问题",
        "- 验证系统的可扩展性和可维护性",
        "",
        "### 1.2 测试范围",
        "- 单元测试",
        "- 集成测试",
        "- 性能测试",
        "- 安全测试",
        "",
        "### 1.3 测试优先级说明",
        "- P0: 阻塞性问题（需立即解决）",
        "- P1: 核心功能问题（影响业务运行）",
        "- P2: 非核心功能问题（影响用户体验）",
        "- P3: 优化类问题（可延后处理）",
        "",
        "### 1.4 测试用例状态",
        "- Not Started: 未开始",
        "- In Progress: 进行中",
        "- Completed: 已完成",
        "- Failed: 未通过",
        "- Blocked: 被阻塞",
        "",
    ]
    
    # 添加测试计划详情
    for priority in ['P0', 'P1', 'P2', 'P3']:
        content.extend([
            f"## {len(content.split('##'))}. {priority}级测试计划",
            ""
        ])
        
        for module, cases in cases_by_priority[priority].items():
            content.extend([
                f"### {module}模块",
                ""
            ])
            
            # 添加测试用例
            for case in cases:
                content.extend([
                    f"#### {case['id']}: {case['name']}",
                    "- **优先级**: " + priority,
                    "- **状态**: " + case['status'],
                    "",
                    "**前置条件**:",
                ])
                
                # 添加前置条件
                for precond in case['preconditions']:
                    content.append(f"- {precond}")
                content.append("")
                
                # 添加测试步骤
                content.append("**测试步骤**:")
                for step in case['steps']:
                    content.append(f"- {step}")
                content.append("")
                
                # 添加预期结果
                content.append("**预期结果**:")
                for result in case['expected_results']:
                    content.append(f"- {result}")
                content.append("")
    
    # 添加测试报告部分
    content.extend([
        "## 测试报告",
        "",
        "### 测试执行统计",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 总用例数：{len(all_cases)}",
        f"- 已完成：{len(get_test_cases(status='Completed'))}",
        f"- 未通过：{len(get_test_cases(status='Failed'))}",
        f"- 未开始：{len(get_test_cases(status='Not Started'))}",
        "",
        "### 优先级分布",
    ])
    
    for priority in ['P0', 'P1', 'P2', 'P3']:
        count = len(get_test_cases(priority=priority))
        content.append(f"- {priority}: {count}个用例")
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

def generate_test_report(output_path: str = "docs/test-report.md"):
    """
    生成测试报告markdown文档。
    
    Args:
        output_path: 输出文件路径
    """
    # 创建输出目录
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 获取所有测试用例
    all_cases = get_test_cases()
    failed_cases = get_test_cases(status='Failed')
    
    # 生成报告内容
    content = [
        "# 测试执行报告",
        "",
        f"## 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 测试概要",
        f"- 总用例数：{len(all_cases)}",
        f"- 已完成：{len(get_test_cases(status='Completed'))}",
        f"- 未通过：{len(failed_cases)}",
        f"- 未开始：{len(get_test_cases(status='Not Started'))}",
        "",
        "## 失败用例详情",
        ""
    ]
    
    # 添加失败用例信息
    for case in failed_cases:
        content.extend([
            f"### {case['id']}: {case['name']}",
            f"- **优先级**: {case['priority']}",
            f"- **模块**: {case['module']}",
            f"- **错误信息**: {case.get('error', 'Unknown error')}",
            ""
        ])
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

if __name__ == "__main__":
    generate_test_plan_md()
    generate_test_report() 