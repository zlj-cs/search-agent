"""
搜索工具模块
使用 Tavily API 进行网络搜索
"""

from typing import Dict, List, Any, Optional
from tavily import TavilyClient
import os


def search(query: str, api_key: Optional[str] = None, search_depth: str = "basic") -> Dict[str, Any]:
    """
    搜索网络信息，返回搜索结果（包含标题、URL和摘要）
    
    Args:
        query: 搜索查询字符串
        api_key: Tavily API密钥，如果不提供则从环境变量TAVILY_API_KEY获取
        search_depth: 搜索深度，可选 "basic" 或 "advanced"
    
    Returns:
        包含搜索结果的字典，格式如下：
        {
            "results": [
                {
                    "title": "网页标题",
                    "url": "网页URL",
                    "content": "网页摘要内容",
                    "score": 相关性分数
                },
                ...
            ]
        }
    """
    # 获取API密钥
    if api_key is None:
        api_key = os.getenv("TAVILY_API_KEY")
    
    if not api_key:
        raise ValueError("请提供 Tavily API 密钥，或设置环境变量 TAVILY_API_KEY")
    
    # 初始化客户端并执行搜索
    client = TavilyClient(api_key=api_key)
    response = client.search(
        query=query,
        search_depth=search_depth
    )
    
    return response


def format_search_results(results: List[Dict[str, Any]]) -> str:
    """
    格式化搜索结果为可读文本
    
    Args:
        results: 搜索结果列表
    
    Returns:
        格式化后的文本字符串
    """
    if not results:
        return "没有找到相关搜索结果。"
    
    formatted = []
    for i, result in enumerate(results, 1):
        formatted.append(f"[{i}] {result.get('title', '无标题')}")
        formatted.append(f"    URL: {result.get('url', '无URL')}")
        formatted.append(f"    摘要: {result.get('content', '无摘要')}")
        formatted.append("")
    
    return "\n".join(formatted)


if __name__ == "__main__":
    # 测试代码
    import json
    
    # 使用示例
    test_query = "环球影城霸天虎过山车游玩时长"
    print(f"搜索查询: {test_query}")
    print("-" * 50)
    
    try:
        result = search(test_query)
        print(format_search_results(result.get("results", [])))
    except Exception as e:
        print(f"搜索出错: {e}")
