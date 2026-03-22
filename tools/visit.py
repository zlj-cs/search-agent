"""
网页访问工具模块
使用 Tavily API 抽取网页内容，并使用大模型进行总结
"""

from typing import Dict, Any, Optional, List
from tavily import TavilyClient
import os
import requests
import json


def extract_webpage_content(urls: List[str], api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    使用 Tavily 抽取网页内容
    
    Args:
        urls: 要抽取的网页URL列表
        api_key: Tavily API密钥，如果不提供则从环境变量TAVILY_API_KEY获取
    
    Returns:
        包含网页内容的字典
    """
    # 获取API密钥
    if api_key is None:
        api_key = os.getenv("TAVILY_API_KEY")
    
    if not api_key:
        raise ValueError("请提供 Tavily API 密钥，或设置环境变量 TAVILY_API_KEY")
    
    # 初始化客户端并抽取内容
    client = TavilyClient(api_key=api_key)
    response = client.extract(urls=urls)
    
    return response


def call_llm_for_summary(
    prompt: str,
    model: str = "gpt-3.5-turbo",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.0
) -> str:
    """
    调用大模型进行内容总结
    
    Args:
        prompt: 提示词
        model: 模型名称
        base_url: API基础URL
        api_key: API密钥
        temperature: 温度参数
    
    Returns:
        模型返回的文本
    """
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if base_url is None:
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature
    }
    
    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=data
    )
    
    response.raise_for_status()
    result = response.json()
    
    return result["choices"][0]["message"]["content"]


def visit(
    url: str,
    goal: str,
    tavily_api_key: Optional[str] = None,
    llm_config: Optional[Dict[str, Any]] = None,
    extraction_prompt_template: str = None
) -> Dict[str, Any]:
    """
    访问网页并根据目标返回内容摘要
    
    Args:
        url: 要访问的网页URL
        goal: 访问此网页的具体信息目标
        tavily_api_key: Tavily API密钥
        llm_config: 大模型配置，包含 model, base_url, api_key, temperature 等
        extraction_prompt_template: 内容抽取提示词模板
    
    Returns:
        包含摘要信息的字典，格式如下：
        {
            "url": "网页URL",
            "goal": "访问目标",
            "summary": "内容摘要",
            "rational": "相关性说明",
            "evidence": "原始证据内容",
            "raw_content": "原始网页内容"
        }
    """
    # 默认LLM配置
    if llm_config is None:
        llm_config = {
            "model": os.getenv("VISIT_MODEL", "gpt-3.5-turbo"),
            "base_url": os.getenv("OPENAI_BASE_URL"),
            "api_key": os.getenv("OPENAI_API_KEY"),
            "temperature": 0.0
        }
    
    # 默认提示词模板
    if extraction_prompt_template is None:
        extraction_prompt_template = """请处理以下网页内容和用户目标，提取相关信息：

## **网页内容**
{webpage_content}

## **用户目标**
{goal}

## **任务指南**
1. **内容扫描**：定位与用户目标直接相关的具体章节/数据
2. **关键提取**：识别并提取最相关的信息。不要遗漏重要信息。尽可能输出完整的原始上下文
3. **摘要输出**：组织成逻辑流畅的简洁段落

## **输出格式**
返回一个JSON对象，包含以下字段：
- "rational": 简要描述哪些章节相关
- "evidence": 提取的相关内容（可以是多个段落）
- "summary": 信息摘要"""
    
    # 抽取网页内容
    extract_result = extract_webpage_content([url], api_key=tavily_api_key)
    
    # 获取原始内容
    raw_content = ""
    if "results" in extract_result:
        for item in extract_result["results"]:
            if item.get("url") == url:
                raw_content = item.get("raw_content", "")
                break
    
    if not raw_content:
        return {
            "url": url,
            "goal": goal,
            "summary": "无法获取网页内容",
            "rational": "",
            "evidence": "",
            "raw_content": "",
            "error": "网页内容抽取失败"
        }
    
    # 构建提示词
    prompt = extraction_prompt_template.format(
        webpage_content=raw_content[:10000],  # 限制内容长度
        goal=goal
    )
    
    # 调用大模型进行总结
    try:
        llm_response = call_llm_for_summary(
            prompt=prompt,
            model=llm_config.get("model"),
            base_url=llm_config.get("base_url"),
            api_key=llm_config.get("api_key"),
            temperature=llm_config.get("temperature", 0.0)
        )
        
        # 尝试解析JSON响应
        try:
            # 提取JSON内容
            json_start = llm_response.find("{")
            json_end = llm_response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                result = json.loads(json_str)
            else:
                result = {"summary": llm_response}
        except json.JSONDecodeError:
            result = {"summary": llm_response}
        
        return {
            "url": url,
            "goal": goal,
            "summary": result.get("summary", ""),
            "rational": result.get("rational", ""),
            "evidence": result.get("evidence", ""),
            "raw_content": raw_content
        }
        
    except Exception as e:
        return {
            "url": url,
            "goal": goal,
            "summary": f"处理失败: {str(e)}",
            "rational": "",
            "evidence": "",
            "raw_content": raw_content,
            "error": str(e)
        }


if __name__ == "__main__":
    # 测试代码
    test_url = "https://www.universalbeijingresort.com.cn/"
    test_goal = "环球影城有哪些游玩项目？"
    
    print(f"测试访问: {test_url}")
    print(f"目标: {test_goal}")
    print("-" * 50)
    
    try:
        result = visit(test_url, test_goal)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"访问出错: {e}")
