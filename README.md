<div align="center">

# QwenWork2API 🚀

**将阿里“千问办公”（QwenWork / 通义千问）无缝转化为 100% 兼容 OpenAI 格式的高性能 2API 代理服务**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![OpenAI Compatible](https://img.shields.io/badge/OpenAI-100%25%20Compatible-00A67E?logo=openai&logoColor=white)](https://platform.openai.com/)

[English](#english) | [中文说明](#中文说明)

</div>

---

## ⚠️ 免责声明 (Disclaimer)

1. **个人学习与研究使用**：本项目仅供个人技术研究、接口兼容性调试与学习交流使用，**严禁用于任何商业营利、非法用途或大规模生产环境**。
2. **版权与商标归属**：本项目涉及的“千问办公”、“通义千问”、“Qwen”等商标、���称及服务版权归其官方所有（阿里巴巴 / 阿里云计算有限公司）。本项目仅为本地格式转换与兼容适配中间件，不对官方服务的稳定性、可用性及数据安全性作任何明示或暗示的保证。
3. **服务条款遵从**：使用者在调用相关接口与服务时，必须严格遵守原服务商的用户协议与服务条款（Terms of Service）。若因使用者自身的不当调用或超额请求引发账号风控、限制或法律纠纷，均由使用者本人独立承担，本项目作者概不负责。

---

<a name="中文说明"></a>
## 💡 为什么需要 QwenWork2API？

阿里“千问办公”（QwenWork）搭载了强大的通义千问最新大模型（如 **Qwen 3.8 Flash** 100 万超长上下文、**Qwen 3.8 Max** 高推理旗舰等），但许多优秀的开源 AI 工具与客户端（如 **OpenCode、Cursor、Claude Code、NextChat、LibreChat、Continue、Dify**）默认只支持标准 OpenAI API 格式。

**QwenWork2API** 是一座轻量级高性能桥梁：
- 零外部重度依赖（基于 Python 3 原生标准库实现，无框架负担）
- 100% 兼容 OpenAI 标准端点 (`/v1/models`, `/v1/chat/completions`)
- 完整支持**真流式 SSE (Server-Sent Events) 输出**、**原生 Function Calling (Tool Calls)** 以及 **Vision 多模态图文输入**
- 针对长任务与高思考模型进行了看门狗和心跳增强，彻底杜绝掉线

---

## 🎯 核心精选模型

本项目去除了过时或冗余的模型，专注于最实用、高能效的核心模型：

| 模型 ID | 对应千问办公档位 | 上下文窗口 | 最大输出 | 特性与适用场景 |
|---|---|---|---|---|
| **`qwen3.8-flash`** (推荐) | **标准 (0.1X)** | **1,048,576 Tokens (1M)** | 65,536 | 极速全能，支持图文理解与工具调用，秒杀日常编码与长文本任务 |
| **`qwen3.8-max`** | **Qwen3.8-Max (1.8X)** | **1,048,576 Tokens (1M)** | 65,536 | 千问最强模型，高深度思考推理，复杂架构重构与长逻辑推导 |
| **`qwen-plus`** | **高级 (1X)** | **131,072 Tokens (128K)** | 8,192 | 性能与成本平衡，擅长多轮对话与文本创作 |

> 别名兼容：请求传入 `qwen-flash` 或 `qwen-max` 时将自动解析为最新的对应版本。

---

## ⚡ 快速开始

### 方式 1：本地直接运行 (最简便)

本项目无需安装任何第三方库，开箱即用：

```bash
# 1. 克隆代码仓库
git clone https://github.com/Alphaxiaoteng/qwenwork2api.git
cd qwenwork2api

# 2. 配置你的百炼 / 通义千问 API Key
export QWENWORK_API_KEY="sk-your-dashscope-api-key"
# 或者复制并编辑 .env 文件
cp .env.example .env

# 3. 启动服务（默认监听 http://127.0.0.1:8796）
python3 main.py
```

### 方式 2：Docker 容器化部署

```bash
# 使用 Docker Compose 一键启动
docker compose up -d

# 或使用原生 Docker 运行
docker build -t qwenwork2api .
docker run -d \
  --name qwenwork2api \
  -p 8796:8796 \
  -e QWENWORK_API_KEY="sk-your-dashscope-api-key" \
  qwenwork2api
```

### 方式 3：macOS 后台守护服务 (LaunchAgent)

创建 `~/Library/LaunchAgents/com.user.qwenwork2api.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.qwenwork2api</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/qwenwork2api/main.py</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>QWENWORK_API_KEY</key>
        <string>sk-your-dashscope-api-key</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

加载守护进程：
```bash
launchctl load ~/Library/LaunchAgents/com.user.qwenwork2api.plist
```

---

## 🛠️ 客户端接入指南

### 1. OpenCode

在你的 `~/.config/opencode/opencode.json` 中添加 Provider：

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
          "name": "Qwen 3.8 Flash (千问办公)",
          "attachment": true,
          "reasoning": true,
          "tool_call": true,
          "limit": {
            "context": 1048576,
            "output": 65536
          },
          "modalities": {
            "input": ["text", "image"],
            "output": ["text"]
          }
        }
      }
    }
  }
}
```

### 2. Cursor / NextChat / LibreChat / Continue

- **API Base URL**: `http://127.0.0.1:8796/v1`
- **API Key**: 任意非空字符串（如 `qwenwork-local`）或直接填入你的百炼 Key
- **Model Name**: `qwen3.8-flash` 或 `qwen3.8-max`

---

## 🧪 接口调用示例

### 1. 查询健康探针
```bash
curl http://127.0.0.1:8796/health
```

### 2. 获取可用模型列表
```bash
curl http://127.0.0.1:8796/v1/models
```

### 3. 流式对��� (SSE)
```bash
curl -N http://127.0.0.1:8796/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-local" \
  -d '{
    "model": "qwen3.8-flash",
    "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己"}],
    "stream": true
  }'
```

---

<a name="english"></a>
## 🌐 English Overview

**QwenWork2API** turns Alibaba QwenWork / DashScope into a 100% OpenAI-compatible 2API proxy.

### ⚠️ Disclaimer

1. **Personal & Educational Use Only**: This project is strictly intended for personal learning, interface compatibility testing, and research purposes. **Any commercial use, illegal activities, or large-scale production deployments are strictly prohibited.**
2. **Trademarks & Copyrights**: All trademarks, brand names, and copyrights (including "QwenWork", "Tongyi Qwen", and "Alibaba") belong to their respective owners (Alibaba Group / Alibaba Cloud). This tool acts solely as a local protocol bridge/adapter and is not officially affiliated with or endorsed by Alibaba.
3. **Compliance with Terms of Service**: Users must strictly comply with the Terms of Service of the respective platforms. The authors assume no liability for any account suspensions, disputes, or damages resulting from the use of this project.

### Features
- **Zero Heavy Dependencies**: Built with Python 3 standard library (`http.server`, `urllib`).
- **OpenAI Specification Compatible**: `GET /v1/models`, `POST /v1/chat/completions`.
- **Full Capabilities**: Streaming (SSE), Native Tool Calls (Function Calling), Vision (Multimodal).
- **Production Grade**: Ready for Docker, macOS LaunchAgent, and systemd.

---

## 📄 License

本项目基于 [MIT 许可证](LICENSE) 开源。欢迎 Star 🌟 与 PR 贡献！
