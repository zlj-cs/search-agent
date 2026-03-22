# Search Agent

一个基于 ReAct 模式的智能搜索助手，能够根据提供的网页搜索接口获取信息并回答用户的问题。

## 项目结构

```
search_agent/
├── agent/                  # 智能体模块
│   ├── __init__.py
│   └── react_agent.py      # ReAct Agent 实现
├── tools/                  # 工具模块
│   ├── __init__.py
│   ├── search.py           # 搜索工具
│   ├── visit.py            # 网页访问工具
│   └── python_interper.py  # Python 执行工具
├── config.yaml             # 配置文件
├── prompts.yaml            # 提示词配置
├── run.py                  # 主入口
├── requirements.txt        # 依赖包
└── README.md               # 说明文档
```

## 功能特点

- **ReAct 模式**：通过推理(Reasoning)和行动(Acting)的循环来完成任务
- **多工具支持**：
  - `search`：网络搜索，返回搜索结果
  - `visit`：访问网页并提取相关信息
  - `python_executor`：执行 Python 代码进行计算
- **结构化输出**：答案包含引用来源和证据
- **易于扩展**：清晰的模块化设计，便于添加新工具

## 环境要求

- **Python**: 3.8 或更高版本
- **操作系统**: macOS / Linux / Windows

## 环境配置

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd search_agent
```

### 2. 创建虚拟环境

**方式一：使用 venv**

macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

**方式二：使用 conda**

```bash
conda create -n search_agent python=3.10
conda activate search_agent
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置 API 密钥

编辑 `config.yaml` 文件，填入你的 API 密钥：

```yaml
# Tavily API 配置（用于搜索和网页抽取）
tavily:
  api_key: "tvly-dev-xxxxx"  # 你的 Tavily API 密钥

# Agent 配置
agent:
  model: "gpt-4o"
  base_url: "https://api.openai.com/v1"
  api_key: "your-api-key"  # 你的 OpenAI API 密钥
  temperature: 0.0
  max_iterations: 10

# Visit 工具配置（用于访问网页并总结）
visit:
  model: "gpt-3.5-turbo"
  base_url: "https://api.openai.com/v1"
  api_key: "your-api-key"  # 你的 OpenAI API 密钥
  temperature: 0.0
```

**获取 API 密钥：**
- Tavily API: https://tavily.com （免费额度可用）
- OpenAI API: https://platform.openai.com
- 也支持其他兼容 OpenAI API 的服务（如 DeepSeek），只需修改 `base_url` 和 `model`

### 5. 验证安装

```bash
python3 run.py --question "1+1=?"
```

如果输出正确结果，说明环境配置成功！

## 使用方法

### 基本使用

```bash
python3 run.py --question "什么是智能体？"
```

### 完整参数

```bash
python3 run.py \
    --question "什么是智能体？" \
    --config config.yaml \
    --prompts prompts.yaml \
    --verbose \
    --output result.json
```

### 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--question` | `-q` | 要问的问题（必填） | - |
| `--config` | `-c` | 配置文件路径 | config.yaml |
| `--prompts` | `-p` | 提示词文件路径 | prompts.yaml |
| `--verbose` | `-v` | 打印详细过程 | False |
| `--output` | `-o` | 输出文件路径 | - |

## 输出格式

Agent 返回结构化的 JSON 答案：

```json
{
  "answer": "对问题的回答",
  "references": [
    {"url": "来源URL", "title": "网页标题"}
  ],
  "evidence": [
    {
      "url": "证据URL",
      "source": "search_snippet 或 page_content",
      "text": "支持答案的证据文本"
    }
  ]
}
```

## 工具说明

### search 工具

搜索网络信息，返回搜索结果（包含标题、URL和摘要）。

```python
# 工具调用格式
{"name": "search", "arguments": {"query": "搜索关键词"}}
```

### visit 工具

访问指定网页，根据目标提取相关信息。

```python
# 工具调用格式
{"name": "visit", "arguments": {"url": "网页URL", "goal": "访问目标"}}
```

### python_executor 工具

在沙箱环境中执行 Python 代码，用于数学计算等场景。

```python
# 工具调用格式
{"name": "python_executor", "arguments": {"code": "```python\nprint(1+1)\n```"}}
```

## 自定义扩展

### 添加新工具

1. 在 `tools/` 目录下创建新的工具文件
2. 在 `tools/__init__.py` 中导入并导出
3. 在 `run.py` 的 `create_tools()` 函数中注册新工具
4. 更新 `prompts.yaml` 中的系统提示词

### 修改提示词

编辑 `prompts.yaml` 文件来自定义系统提示词和网页抽取提示词。

## 常见问题

### 1. pip 命令找不到

尝试使用 `pip3` 代替 `pip`：
```bash
pip3 install -r requirements.txt
```

### 2. SSL 警告

如果看到 OpenSSL 相关警告，可以忽略，不影响正常使用。

### 3. API 调用失败

- 检查 API 密钥是否正确
- 检查网络是否能访问对应 API
- 检查 `base_url` 是否正确（需要包含 `/v1` 后缀）

## 注意事项

1. **API 密钥安全**：请勿将 API 密钥提交到版本控制系统
2. **网络访问**：确保能够访问 Tavily API 和对应的 LLM API
3. **成本控制**：每次查询可能产生多次 API 调用，注意控制成本
4. **超时设置**：复杂查询可能需要较长时间，可在配置中调整 `max_iterations`

## 许可证

MIT License
