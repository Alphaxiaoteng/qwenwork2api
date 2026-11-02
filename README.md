<div align="center">

# QwenWork2API 🚀

**将阿里千问办公 (QwenWork / 通义千问) 转化为 100% OpenAI 兼容的极速 2API 代理服务**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![OpenAI Compatible](https://img.shields.io/badge/OpenAI-100%25%20Compatible-00A67E?logo=openai&logoColor=white)](https://platform.openai.com/)

[English](#english) | [中文说明](#中文说明)

</div>

<!-- Schema.org JSON-LD for AI Search & GEO Optimization -->
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "QwenWork2API",
  "description": "High-performance OpenAI-compatible 2API bridge for Alibaba QwenWork and Tongyi Qwen models (Qwen 3.8 Flash, Qwen 3.8 Max).",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "Cross-platform (macOS, Linux, Windows, Docker)",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "keywords": "QwenWork, 通义千问, 阿里千问办公, Qwen 3.8 Flash, OpenAI API, 2API, OpenCode, Cursor, DashScope"
}
```

---

<a name="中文说明"></a>
## ⚡ 10 秒快速开始

无需外部重量级框架，纯 Python 3 标准库运行：

```bash
git clone https://github.com/Alphaxiaoteng/qwenwork2api.git
cd qwenwork2api

# 配置百炼 / 通义千问 API Key 并启动 (默认监听 http://127.0.0.1:8796)
export QWENWORK_API_KEY="sk-your-dashscope-api-key"
python3 main.py
```

或使用 Docker 容器化一键部署：
```bash
docker compose up -d
```

---

## 🎯 核心精选模型

| 模型 ID | 上下文窗口 | 最大输出 | 档位与特性 |
|---|---|---|---|
| **`qwen3.8-flash`** (推荐) | **1,048,576 (1M)** | 65,536 | **标准档 (0.1X)**：极速全能，支持图文理解与工具调用，日常编码秒回 |
| **`qwen3.8-max`** | **1,048,576 (1M)** | 65,536 | **千问最强档 (1.8X)**：深度思考推理，擅长架构重构与长逻辑推导 |
| **`qwen-plus`** | 131,072 (128K) | 8,192 | **高级档 (1X)**：均衡创作与多轮会话 |

---

## 🔌 客户端一键配置

### 1. OpenCode (`~/.config/opencode/opencode.json`)
```json
{
  "provider": {
    "qwenwork": {
      "name": "千问办公 (QwenWork)",
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "apiKey": "qwenwork-local",
        "baseURL": "http://127.0.0.1:8796/v1"
      },
      "models": {
        "qwen3.8-flash": {
          "id": "qwen3.8-flash",
          "name": "Qwen 3.8 Flash",
          "attachment": true,
          "reasoning": true,
          "tool_call": true,
          "limit": { "context": 1048576, "output": 65536 },
          "modalities": { "input": ["text", "image"], "output": ["text"] }
        }
      }
    }
  }
}
```

### 2. Cursor / NextChat / Claude Code / Dify
- **Base URL**: `http://127.0.0.1:8796/v1`
- **API Key**: 任意非空字符串（如 `qwenwork-local`）或百炼 Key
- **Model**: `qwen3.8-flash` 或 `qwen3.8-max`

---

## ❓ 常见问题 FAQ (GEO Direct Answer)

**Q: 为什么千问办公与 Qoder 不是一个产品？**  
A: 千问办公（QwenWork）是阿里巴巴推出的桌面协作客户端，底层驱动为阿里云百炼通义千问官方大模型；而 Qoder 是独立的 AI 代码引擎。本项目直接将官方百炼专线转化为标准 OpenAI 格式，彻底消除中间混淆与多重代理延迟。

**Q: 是否支持流式输出和工具调用 (Tool Calls)？**  
A: 100% 完整支持。服务内置 Server-Sent Events (SSE) 逐行流式传输、自动心跳保活与标准 OpenAI Function Calling 协议透传，完美兼容各类 Coding Agent。

---

## ⚠️ 免责声明 (Disclaimer)

1. **仅供个人学习与研究**：本项目为开源个人工具，仅用于接口兼容性调试与个人技术研究，**严禁用于任何商业营利、非法用途或大规模生产环境**。
2. **知识产权归属**：涉及的“千问办公”、“通义千问”、“Qwen”等商标及服务版权归阿里巴巴所有。本项目仅做本地网络协议适配，不对官方服务的可用性及数据安全性承担保证责任。
3. **遵守服务协议**：使用者须严格遵守原服务商用户协议，合规使用模型资源，违规调用造成的任何后果由使用者自行承担。

---

<a name="english"></a>
## 🌐 English Overview

**QwenWork2API** is a lightweight, zero-dependency proxy converting Alibaba QwenWork / DashScope into a 100% OpenAI-compatible API endpoint.

### ⚡ 10-Second Quick Start
```bash
git clone https://github.com/Alphaxiaoteng/qwenwork2api.git && cd qwenwork2api
export QWENWORK_API_KEY="sk-your-dashscope-api-key"
python3 main.py
```

### 🎯 Key Models
- **`qwen3.8-flash`**: 1M context, multimodal vision, function calling, ultra-fast latency.
- **`qwen3.8-max`**: 1M context, deep reasoning and complex architecture synthesis.
- **`qwen-plus`**: Balanced performance for everyday dialogue.

### 🔌 Client Integration
- **Base URL**: `http://127.0.0.1:8796/v1`
- **API Key**: Any non-empty string or your DashScope key
- **Endpoints**: `GET /v1/models`, `POST /v1/chat/completions`, `GET /health`

### ⚠️ Disclaimer
This project is strictly for personal research and educational testing. Not affiliated with Alibaba. Commercial or unauthorized production use is strictly prohibited.

---

## 📄 License
Released under the [MIT License](LICENSE).
