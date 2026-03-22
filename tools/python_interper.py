"""
Python执行工具模块
在沙箱环境中执行Python代码，用于数学计算等场景
"""

from typing import Dict, Any, Optional
import subprocess
import tempfile
import os
import json
import re


def python_executor(code: str, timeout: int = 30) -> Dict[str, Any]:
    """
    在沙箱环境中执行Python代码
    
    Args:
        code: 要执行的Python代码（可以包含 ```python ... ``` 代码块标记）
        timeout: 执行超时时间（秒）
    
    Returns:
        包含执行结果的字典：
        {
            "success": True/False,
            "output": "标准输出内容",
            "error": "错误信息（如果有）",
            "return_value": "返回值（如果有）"
        }
    """
    # 清理代码（去除代码块标记）
    code = clean_code(code)
    
    # 安全检查
    safety_check_result = check_code_safety(code)
    if not safety_check_result["safe"]:
        return {
            "success": False,
            "output": "",
            "error": f"安全检查失败: {safety_check_result['reason']}",
            "return_value": None
        }
    
    # 创建临时文件执行代码
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(code)
            temp_file = f.name
        
        # 执行代码
        result = subprocess.run(
            ['python3', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # 清理临时文件
        os.unlink(temp_file)
        
        if result.returncode == 0:
            return {
                "success": True,
                "output": result.stdout,
                "error": "",
                "return_value": None
            }
        else:
            return {
                "success": False,
                "output": result.stdout,
                "error": result.stderr,
                "return_value": None
            }
            
    except subprocess.TimeoutExpired:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        return {
            "success": False,
            "output": "",
            "error": f"执行超时（超过{timeout}秒）",
            "return_value": None
        }
    except Exception as e:
        if 'temp_file' in locals() and os.path.exists(temp_file):
            os.unlink(temp_file)
        return {
            "success": False,
            "output": "",
            "error": f"执行出错: {str(e)}",
            "return_value": None
        }


def clean_code(code: str) -> str:
    """
    清理代码，去除代码块标记
    
    Args:
        code: 可能包含代码块标记的代码
    
    Returns:
        清理后的代码
    """
    # 去除 ```python 和 ``` 标记
    code = re.sub(r'^```python\s*', '', code.strip())
    code = re.sub(r'^```\s*', '', code)
    code = re.sub(r'\s*```$', '', code)
    return code.strip()


def check_code_safety(code: str) -> Dict[str, Any]:
    """
    检查代码安全性
    
    Args:
        code: 要检查的Python代码
    
    Returns:
        安全检查结果
    """
    # 危险操作列表
    dangerous_patterns = [
        r'import\s+os',
        r'from\s+os\s+import',
        r'import\s+subprocess',
        r'from\s+subprocess\s+import',
        r'import\s+sys',
        r'from\s+sys\s+import',
        r'import\s+shutil',
        r'from\s+shutil\s+import',
        r'open\s*\([^)]*,\s*["\']w["\']',  # 写文件
        r'open\s*\([^)]*,\s*["\']a["\']',  # 追加文件
        r'exec\s*\(',
        r'eval\s*\(',
        r'__import__',
        r'globals\s*\(',
        r'locals\s*\(',
        r'compile\s*\(',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, code):
            return {
                "safe": False,
                "reason": f"代码包含潜在危险操作: {pattern}"
            }
    
    return {"safe": True, "reason": ""}


def format_execution_result(result: Dict[str, Any]) -> str:
    """
    格式化执行结果为可读文本
    
    Args:
        result: 执行结果字典
    
    Returns:
        格式化后的文本
    """
    if result["success"]:
        output = f"执行成功！\n"
        if result["output"]:
            output += f"输出:\n{result['output']}"
        return output
    else:
        return f"执行失败！\n错误: {result['error']}"


if __name__ == "__main__":
    # 测试代码
    test_codes = [
        """
```python
print("Hello, World!")
```
""",
        """
```python
import math
result = math.sqrt(16)
print(f"16的平方根是: {result}")
```
""",
        """
```python
# 计算斐波那契数列
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
```
""",
    ]
    
    for i, code in enumerate(test_codes, 1):
        print(f"\n测试 {i}:")
        print("-" * 50)
        result = python_executor(code)
        print(format_execution_result(result))
