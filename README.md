# Search Agent

<p align="center">
  <em>一个简洁易懂的 ReAct 智能搜索助手，适合初学者学习 AI Agent 开发</em>
</p>

<p align="center">
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white" alt="Python Version">
  </a>
  <a href="https://github.com/zlj-cs/search-agent/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  </a>
  <a href="https://github.com/zlj-cs/search-agent/stargazers">
    <img src="https://img.shields.io/github/stars/zlj-cs/search-agent?style=social" alt="GitHub Stars">
  </a>
</p>

---

## 🎯 项目简介

Search Agent 是一个基于 **ReAct (Reasoning + Acting)** 模式的智能搜索助手。它能通过搜索网络、访问网页、执行 Python 代码来回答用户问题，并输出结构化的答案（包含引用来源和证据）。

**适合人群**：想要学习 AI Agent 开发的初学者

**核心特点**：
- 📖 **代码结构清晰**：模块化设计，注释详细，易于理解
- 🔧 **三种工具**：搜索、网页访问、Python 计算
- 📝 **结构化输出**：答案包含引用和证据，可追溯
- 🚀 **易于扩展**：轻松添加新工具和自定义功能

---

## 📸 效果演示

### 数学计算
```bash
$ python3 run.py --question "123*456=?"

============================================================
问题: 123*456=?
============================================================

--- 第 1 轮 ---
[工具调用] python_executor({'code': 'result = 123 * 456\nprint(result)'})
[工具结果] 56088

--- 第 2 轮 ---
{
  "answer": "123 × 456 = 56,088",
  "references": [],
  "evidence": []
}
```

### 网络搜索
```bash
$ python3 run.py --question "什么是智能体？"

============================================================
问题: 什么是智能体？
============================================================

--- 第 1 轮 ---
[工具调用] search({'query': '什么是智能体 定义'})

--- 第 2 轮 ---
[工具调用] visit({'url': 'https://...', 'goal': '获取智能体的定义'})

--- 第 3 轮 ---
{
  "answer": "智能体（Agent）是指能够感知环境并自主采取行动以实现特定目标的实体...",
  "references": [
    {"url": "https://...", "title": "什么是智能体？"}
  ],
  "evidence": [
    {"url": "https://...", "source": "page_content", "text": "..."}
  ]
}
```

---

## 🏗️ 项目结构

```
search_agent/
├── agent/                  # 智能体模块
│   ├── __init__.py
│   └── react_agent.py      # ReAct Agent 实现
├── tools/                  # 工具模块
│   ├── __init__.py
│   ├── search.py           # 搜索工具 (Tavily API)
│   ├── visit.py            # 网页访问工具
│   └── python_interper.py  # Python 执行工具
├── config.yaml             # 配置文件
├── prompts.yaml            # 提示词配置
├── run.py                  # 主入口
├── requirements.txt        # 依赖包
└── README.md               # 说明文档
```

---

## ✨ 功能特点

| 功能 | 说明 |
|------|------|
| 🔍 **search** | 搜索网络信息，返回搜索结果（标题、URL、摘要） |
| 🌐 **visit** | 访问指定网页，根据目标提取相关信息 |
| 🐍 **python_executor** | 在沙箱环境中执行 Python 代码进行计算 |

---

## 📋 环境要求

- **Python**: 3.8 或更高版本
- **操作系统**: macOS / Linux / Windows

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/zlj-cs/search-agent.git
cd search-agent
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
  api_key: "your-api-key"  # 你的 API 密钥
  temperature: 0.0
  max_iterations: 10
```

**获取 API 密钥：**
- Tavily API: https://tavily.com （免费额度可用）
- OpenAI API: https://platform.openai.com
- 也支持其他兼容 OpenAI API 的服务（如 DeepSeek），只需修改 `base_url` 和 `model`

### 5. 验证安装

```bash
python3 run.py --question "1+1=?"
```

如果输出正确结果，说明环境配置成功！🎉

---

## 📖 使用方法

### 基本使用

```bash
python3 run.py --question "什么是智能体？"
```

### 完整参数

```bash
python3 run.py \
    --question "北京环球影城有哪些项目？" \
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

---

## 📤 输出格式

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

---

## 🛠️ 自定义扩展

### 添加新工具

1. 在 `tools/` 目录下创建新的工具文件
2. 在 `tools/__init__.py` 中导入并导出
3. 在 `run.py` 的 `create_tools()` 函数中注册新工具
4. 更新 `prompts.yaml` 中的系统提示词

### 修改提示词

编辑 `prompts.yaml` 文件来自定义系统提示词和网页抽取提示词。

---

## ❓ 常见问题

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

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## ⚠️ 注意事项

1. **API 密钥安全**：请勿将 API 密钥提交到版本控制系统
2. **网络访问**：确保能够访问 Tavily API 和对应的 LLM API
3. **成本控制**：每次查询可能产生多次 API 调用，注意控制成本

---

## 📄 许可证

[MIT License](LICENSE)

---

<p align="center">
  如果这个项目对你有帮助，请给一个 ⭐️ Star 支持一下！
</p>
