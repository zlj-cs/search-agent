"""
ReAct Agent 模块
基于 ReAct (Reasoning + Acting) 模式的智能体实现
"""

from typing import Dict, Any, Optional, List, Callable
import json
import re
import requests
from datetime import datetime


class ReactAgent:
    """
    基于 ReAct 模式的搜索智能体
    
    通过推理(Reasoning)和行动(Acting)的循环来完成任务：
    1. 思考：分析当前情况，决定下一步行动
    2. 行动：调用工具执行操作
    3. 观察：获取工具执行结果
    4. 重复以上步骤直到得出最终答案
    """
    
    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str,
        temperature: float = 0.0,
        max_iterations: int = 10,
        tools: Optional[Dict[str, Callable]] = None,
        system_prompt: Optional[str] = None
    ):
        """
        初始化 ReAct Agent
        
        Args:
            model: 模型名称（如 "gpt-4", "gpt-3.5-turbo"）
            base_url: API 请求的基础 URL
            api_key: API 密钥
            temperature: 温度参数，控制输出的随机性
            max_iterations: 对话的最大轮次
            tools: 工具函数字典，键为工具名，值为可调用函数
            system_prompt: 系统提示词
        """
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.temperature = temperature
        self.max_iterations = max_iterations
        self.tools = tools or {}
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        # 对话历史
        self.messages: List[Dict[str, str]] = []
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        current_date = datetime.now().strftime("%Y年%m月%d日")
        prompt = """你是一个深度研究助手。你的核心功能是对任何主题进行彻底的多源调查。你需要处理广泛的开放领域查询和专业学术领域的问题。对于每个请求，你需要从可信、多样的来源综合信息，提供全面、准确、客观的回答。

# 工具

你可以调用一个或多个函数来帮助回答用户问题。

你可以在 <tools></tools> XML 标签中查看函数描述：
<tools>
{"type": "function", "function": {"name": "search", "description": "搜索网络信息。返回搜索结果，包含标题、URL和摘要。", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "搜索查询字符串"}}, "required": ["query"]}}}
{"type": "function", "function": {"name": "visit", "description": "访问网页并根据目标返回内容摘要。", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "要访问的网页URL"}, "goal": {"type": "string", "description": "访问此网页的具体信息目标"}}, "required": ["url", "goal"]}}}
{"type": "function", "function": {"name": "python_executor", "description": "在沙箱环境中执行Python代码。用于计算、数据处理或分析。只能使用标准库。使用print()输出。", "parameters": {"type": "object", "properties": {"code": {"type": "string", "description": "要执行的Python代码，用```python ... ```代码块包裹"}}, "required": ["code"]}}}
</tools>

每次函数调用，请在 ```json ``` 代码块中返回JSON对象：
```json
{"name": "<函数名>", "arguments": <参数JSON对象>}
```

# 响应格式

当你收集了足够的信息并准备给出最终答案时，请将整个答案放在 <answer></answer> 标签中，使用 JSON 格式输出：

<answer>
```json
{
  "answer": "你对问题的回答",
  "references": [
    {"url": "支持你答案的来源URL1", "title": "网页标题1"},
    {"url": "支持你答案的来源URL2", "title": "网页标题2"}
  ],
  "evidence": [
    {"url": "证据来源URL1", "source": "search_snippet", "text": "从搜索结果摘要中看到的支持答案的文本"},
    {"url": "证据来源URL2", "source": "page_content", "text": "通过visit工具访问网页后看到的支持答案的原文"}
  ]
}
```
</answer>

**说明**：
- references 和 evidence 都是数组，可以包含 1 条或多条记录
- 每条 reference 包含 url（必填）和 title（可选）
- 每条 evidence 包含：
  - url：证据来源URL
  - source：来源类型，必须是 "search_snippet"（来自搜索摘要）或 "page_content"（来自visit网页正文）
  - text：你实际看到的支持答案的文本内容

# 重要规则

1. 你可以使用提供的工具（search、visit、python_executor）来获取真实信息或进行必要的计算。不要编造或幻觉任何信息。
2. 在执行必要的工具调用并获得真实结果之前，不要提供 <answer>。
3. 每次响应应该只包含工具调用或 <answer>，不能同时包含两者。
4. 如果不确定某些信息，请搜索更多信息而不是猜测。
5. 使用 python_executor 进行复杂计算、数据分析或处理数值数据。
6. **关键要求**：你的答案必须包含：
   - answer: 对问题的清晰回答
   - references: 参考URL列表（至少1条，可以有多条）
   - evidence: 证据列表（至少1条，可以有多条）
7. **证据诚实性要求**：
   - 如果证据来自 search 工具返回的摘要，source 填 "search_snippet"
   - 如果证据来自 visit 工具访问网页后看到的正文，source 填 "page_content"
   - 如果对同一个URL既看了摘要又访问了正文，优先用正文内容，source 填 "page_content"
   - 不要把搜索摘要伪装成网页正文引用，也不要编造未看到过的内容
8. **JSON格式要求**：URL 必须是完整的字符串，不能换行。

当前日期: """ + current_date
        return prompt
    
    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        调用大语言模型
        
        Args:
            messages: 对话消息列表
        
        Returns:
            模型返回的文本
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        
        response.raise_for_status()
        result = response.json()
        
        return result["choices"][0]["message"]["content"]
    
    def _extract_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """
        从模型响应中提取工具调用
        
        Args:
            response: 模型响应文本
        
        Returns:
            工具调用字典，如果没有工具调用则返回 None
        """
        # 尝试匹配 JSON 代码块
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        matches = re.findall(json_pattern, response)
        
        for match in matches:
            try:
                tool_call = json.loads(match.strip())
                if "name" in tool_call and "arguments" in tool_call:
                    return tool_call
            except json.JSONDecodeError:
                continue
        
        # 尝试直接解析 JSON
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                tool_call = json.loads(response[json_start:json_end])
                if "name" in tool_call and "arguments" in tool_call:
                    return tool_call
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _extract_answer(self, response: str) -> Optional[Dict[str, Any]]:
        """
        从模型响应中提取最终答案
        
        Args:
            response: 模型响应文本
        
        Returns:
            答案字典，如果没有答案则返回 None
        """
        # 匹配 <answer> 标签
        answer_pattern = r'<answer>\s*([\s\S]*?)\s*</answer>'
        match = re.search(answer_pattern, response)
        
        if match:
            answer_content = match.group(1).strip()
            # 提取 JSON
            json_pattern = r'```json\s*([\s\S]*?)\s*```'
            json_match = re.search(json_pattern, answer_content)
            
            if json_match:
                try:
                    return json.loads(json_match.group(1).strip())
                except json.JSONDecodeError:
                    pass
            else:
                # 尝试直接解析
                try:
                    return json.loads(answer_content)
                except json.JSONDecodeError:
                    return {"answer": answer_content}
        
        return None
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        执行工具调用
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
        
        Returns:
            工具执行结果（字符串形式）
        """
        if tool_name not in self.tools:
            return f"错误：未知的工具 '{tool_name}'。可用工具：{list(self.tools.keys())}"
        
        try:
            result = self.tools[tool_name](**arguments)
            
            # 将结果转换为字符串
            if isinstance(result, str):
                return result
            elif isinstance(result, dict):
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                return str(result)
                
        except Exception as e:
            return f"工具执行错误：{str(e)}"
    
    def run(self, question: str, verbose: bool = True) -> Dict[str, Any]:
        """
        运行 Agent 处理用户问题
        
        Args:
            question: 用户问题
            verbose: 是否打印详细过程
        
        Returns:
            最终答案字典
        """
        # 初始化消息
        self.messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": question}
        ]
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"问题: {question}")
            print(f"{'='*60}\n")
        
        iteration = 0
        final_answer = None
        
        while iteration < self.max_iterations:
            iteration += 1
            
            if verbose:
                print(f"\n--- 第 {iteration} 轮 ---")
            
            # 调用 LLM
            try:
                response = self._call_llm(self.messages)
            except Exception as e:
                return {
                    "answer": f"调用模型失败: {str(e)}",
                    "references": [],
                    "evidence": [],
                    "error": str(e)
                }
            
            if verbose:
                print(f"\n[模型响应]\n{response}\n")
            
            # 检查是否有最终答案
            answer = self._extract_answer(response)
            if answer:
                final_answer = answer
                break
            
            # 检查是否有工具调用
            tool_call = self._extract_tool_call(response)
            if tool_call:
                tool_name = tool_call["name"]
                arguments = tool_call["arguments"]
                
                if verbose:
                    print(f"[工具调用] {tool_name}({arguments})")
                
                # 执行工具
                tool_result = self._execute_tool(tool_name, arguments)
                
                if verbose:
                    print(f"[工具结果]\n{tool_result[:500]}{'...' if len(tool_result) > 500 else ''}\n")
                
                # 添加到消息历史
                self.messages.append({"role": "assistant", "content": response})
                self.messages.append({"role": "user", "content": f"工具执行结果：\n{tool_result}"})
            else:
                # 没有工具调用也没有答案，可能是模型不理解
                if verbose:
                    print("[警告] 模型响应中既没有工具调用也没有最终答案")
                
                # 尝试引导模型
                self.messages.append({"role": "assistant", "content": response})
                self.messages.append({
                    "role": "user",
                    "content": "请使用提供的工具来获取信息，或者给出最终答案（使用<answer>标签）。"
                })
        
        if final_answer is None:
            final_answer = {
                "answer": "达到最大迭代次数，未能得出最终答案。",
                "references": [],
                "evidence": [],
                "iterations": iteration
            }
        
        if verbose:
            print(f"\n{'='*60}")
            print("最终答案:")
            print(f"{'='*60}")
            print(json.dumps(final_answer, ensure_ascii=False, indent=2))
        
        return final_answer
    
    def reset(self):
        """重置 Agent 状态"""
        self.messages = []


if __name__ == "__main__":
    # 简单测试
    print("ReactAgent 模块加载成功")
    print("请通过 run.py 运行完整的智能体")
