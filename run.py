#!/usr/bin/env python3
"""
Search Agent 主入口
使用方法: python3 run.py --question "你的问题"
"""

import argparse
import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional

import yaml

from agent import ReactAgent
from tools import search, visit, python_executor


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 替换环境变量
    config = replace_env_vars(config)
    
    return config


def replace_env_vars(config: Any) -> Any:
    """
    递归替换配置中的环境变量
    
    Args:
        config: 配置值
    
    Returns:
        替换后的配置
    """
    if isinstance(config, dict):
        return {k: replace_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [replace_env_vars(item) for item in config]
    elif isinstance(config, str):
        # 匹配 ${ENV_VAR} 格式
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, config)
        for match in matches:
            env_value = os.getenv(match, "")
            config = config.replace(f"${{{match}}}", env_value)
        return config
    else:
        return config


def load_prompts(prompts_path: str = "prompts.yaml") -> Dict[str, str]:
    """
    加载提示词文件
    
    Args:
        prompts_path: 提示词文件路径
    
    Returns:
        提示词字典
    """
    with open(prompts_path, 'r', encoding='utf-8') as f:
        prompts = yaml.safe_load(f)
    
    return prompts


def create_tools(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建工具函数字典
    
    Args:
        config: 配置字典
    
    Returns:
        工具函数字典
    """
    tavily_api_key = config.get("tavily", {}).get("api_key")
    visit_config = config.get("visit", {})
    
    def search_tool(query: str) -> str:
        """搜索工具"""
        result = search(query, api_key=tavily_api_key)
        # 格式化返回结果
        formatted_results = []
        for item in result.get("results", []):
            formatted_results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": item.get("score", 0)
            })
        return json.dumps({"results": formatted_results}, ensure_ascii=False, indent=2)
    
    def visit_tool(url: str, goal: str) -> str:
        """访问网页工具"""
        result = visit(
            url=url,
            goal=goal,
            tavily_api_key=tavily_api_key,
            llm_config={
                "model": visit_config.get("model"),
                "base_url": visit_config.get("base_url"),
                "api_key": visit_config.get("api_key"),
                "temperature": visit_config.get("temperature", 0.0)
            }
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def python_tool(code: str) -> str:
        """Python执行工具"""
        result = python_executor(code)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    return {
        "search": search_tool,
        "visit": visit_tool,
        "python_executor": python_tool
    }


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="Search Agent - 智能搜索助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python3 run.py --question "什么是智能体？"
  python3 run.py --question "北京环球影城有哪些项目？" --config config.yaml
  python3 run.py -q "1+1等于几？" --verbose
        """
    )
    
    parser.add_argument(
        "-q", "--question",
        type=str,
        required=True,
        help="要问的问题"
    )
    
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="config.yaml",
        help="配置文件路径（默认: config.yaml）"
    )
    
    parser.add_argument(
        "-p", "--prompts",
        type=str,
        default="prompts.yaml",
        help="提示词文件路径（默认: prompts.yaml）"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="打印详细过程"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="输出文件路径（可选，将结果保存到文件）"
    )
    
    args = parser.parse_args()
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 切换到脚本目录
    os.chdir(script_dir)
    
    # 加载配置
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"错误：配置文件 '{args.config}' 不存在")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"错误：配置文件格式错误: {e}")
        sys.exit(1)
    
    # 加载提示词
    try:
        prompts = load_prompts(args.prompts)
    except FileNotFoundError:
        print(f"错误：提示词文件 '{args.prompts}' 不存在")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"错误：提示词文件格式错误: {e}")
        sys.exit(1)
    
    # 检查必要的 API 密钥
    agent_config = config.get("agent", {})
    if not agent_config.get("api_key"):
        print("错误：未配置 OpenAI API 密钥")
        print("请在 config.yaml 中设置 api_key，或设置环境变量 OPENAI_API_KEY")
        sys.exit(1)
    
    # 准备系统提示词
    current_date = datetime.now().strftime("%Y年%m月%d日")
    system_prompt = prompts.get("system_prompt", "").replace("{{current_date}}", current_date)
    
    # 创建工具
    tools = create_tools(config)
    
    # 创建 Agent
    agent = ReactAgent(
        model=agent_config.get("model", "gpt-4"),
        base_url=agent_config.get("base_url", "https://api.openai.com/v1"),
        api_key=agent_config.get("api_key"),
        temperature=agent_config.get("temperature", 0.0),
        max_iterations=agent_config.get("max_iterations", 10),
        tools=tools,
        system_prompt=system_prompt
    )
    
    # 运行 Agent
    verbose = args.verbose or config.get("verbose", True)
    result = agent.run(args.question, verbose=verbose)
    
    # 保存结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {args.output}")
    
    return result


if __name__ == "__main__":
    main()
