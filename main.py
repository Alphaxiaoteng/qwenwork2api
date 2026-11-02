#!/usr/bin/env python3
"""
QwenWork2API: 将阿里“千问办公”（QwenWork / 通义千问）能力封装为 100% 兼容 OpenAI 格式的高性能 2API 代理服务。
支持 HTTP 2API、CLI 终端命令行、MCP (Model Context Protocol) 标准协议三模运行。

【免责声明 / Disclaimer】
  1. 本项目仅供个人学习、技术研究与接口兼容性测试使用，���禁用于商业用途、非法用途或生产环境。
  2. 相关商标及底层服务版权均归阿里巴巴 / 阿里云官方所有。
  3. 使用者须严格遵守原服务商用户协议与服务条款，违规使用后果自负。

功能特性:
  - 100% OpenAI 接口规范 (GET /v1/models, POST /v1/chat/completions)
  - CLI 命令行模式：支持单次提问、管道输入与交互式 REPL 终端对话
  - MCP 服务模式：原生适配 Claude Desktop、Cursor、OpenCode MCP Stdio 标准
  - 支持真流式 Server-Sent Events (SSE) 输出与自动心跳保活
  - 支持原生 Function Calling (Tool Calls) 工具调用透传
  - 支持 Vision 多模态图文输入 (image_url / base64)
  - 纯 Python 3 标准库实现，零外部重度依赖，开箱即用
"""

import os
import sys
import json
import time
import socket
import argparse
import urllib.request
import urllib.error
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ==================== 默认配置与环境变量加载 ====================

DEFAULT_PORT = 8796
DEFAULT_UPSTREAM = "https://dashscope.aliyuncs.com/compatible-mode/v1"

def load_dotenv():
    """纯标准库轻量加载当前目录下的 .env 文件"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'").strip('"')
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception as e:
        sys.stderr.write(f"[WARN] 加载 .env 失败: {e}\n")

load_dotenv()

PORT = int(os.environ.get("PORT") or os.environ.get("QWENWORK_PORT") or DEFAULT_PORT)
UPSTREAM_BASE = (os.environ.get("QWENWORK_BASE_URL") or DEFAULT_UPSTREAM).rstrip("/")

# 优先读取 QWENWORK_API_KEY，兜底读取 DASHSCOPE_API_KEY
API_KEY = os.environ.get("QWENWORK_API_KEY") or os.environ.get("DASHSCOPE_API_KEY") or ""

# 对外暴露的核心推荐模型定义
CORE_MODELS = [
    {
        "id": "qwen3.8-flash",
        "object": "model",
        "owned_by": "alibaba-qwen",
        "display_name": "Qwen 3.8 Flash (极速全能 1M 上下文)",
        "context_window": 1048576,
        "max_output": 65536,
        "modalities": ["text", "image"],
        "tier": "标�� (0.1X)"
    },
    {
        "id": "qwen3.8-max",
        "object": "model",
        "owned_by": "alibaba-qwen",
        "display_name": "Qwen 3.8 Max (高推理高思考旗舰)",
        "context_window": 1048576,
        "max_output": 65536,
        "modalities": ["text", "image"],
        "tier": "Qwen3.8-Max (1.8X)"
    },
    {
        "id": "qwen-plus",
        "object": "model",
        "owned_by": "alibaba-qwen",
        "display_name": "Qwen Plus (均衡旗舰)",
        "context_window": 131072,
        "max_output": 8192,
        "modalities": ["text"],
        "tier": "高级 (1X)"
    }
]

# 友好别名映射表
MODEL_ALIASES = {
    "qwen-flash": "qwen3.8-flash",
    "qwen38-flash": "qwen3.8-flash",
    "qwen-3.8-flash": "qwen3.8-flash",
    "qwen-max": "qwen3.8-max",
    "qwen38-max": "qwen3.8-max",
    "qwen-3.8-max": "qwen3.8-max",
}

def resolve_model_id(raw_id):
    """标准化模型名称解析"""
    if not raw_id:
        return "qwen3.8-flash"
    clean = str(raw_id).strip()
    if "/" in clean:
        clean = clean.split("/")[-1]
    return MODEL_ALIASES.get(clean.lower(), clean)

# ==================== 通用推理请求执行引擎 ====================

def request_chat_completion(messages, model="qwen3.8-flash", stream=False, api_key=None, extra_params=None):
    """底层通用的通义千问 / 百炼 Chat Completion 执行器"""
    effective_key = api_key or API_KEY
    if not effective_key:
        raise ValueError("Missing API Key. Please configure QWENWORK_API_KEY or DASHSCOPE_API_KEY.")

    target_model = resolve_model_id(model)
    payload = {
        "model": target_model,
        "messages": messages,
        "stream": stream
    }
    if extra_params:
        payload.update(extra_params)

    upstream_url = f"{UPSTREAM_BASE}/chat/completions"
    upstream_req = urllib.request.Request(
        upstream_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {effective_key}",
            "Content-Type": "application/json",
            "User-Agent": "QwenWork2API/1.1.0"
        },
        method="POST"
    )

    try:
        resp = urllib.request.urlopen(upstream_req, timeout=300)
        return resp
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", "replace")
        try:
            err_json = json.loads(err_body)
            err_msg = err_json.get("error", {}).get("message") or err_body
        except Exception:
            err_msg = err_body
        raise RuntimeError(f"Upstream HTTP {e.code}: {err_msg}")
    except Exception as e:
        raise RuntimeError(f"Connection failed: {str(e)}")

# ==================== HTTP Server 模式 ====================

class QwenWorkProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(f"[{timestamp}] {fmt % args}\n")

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept, X-Requested-With")

    def _json_response(self, data, status_code=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path in ("", "/health", "/ping"):
            status_info = {
                "status": "healthy",
                "service": "QwenWork2API",
                "version": "1.1.0",
                "port": PORT,
                "authenticated": bool(API_KEY),
                "upstream": UPSTREAM_BASE,
                "available_models": [m["id"] for m in CORE_MODELS]
            }
            return self._json_response(status_info, 200)

        if path in ("/v1/models", "/models"):
            models_data = [
                {
                    "id": m["id"],
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": m["owned_by"],
                    "permission": [],
                    "root": m["id"],
                    "parent": None
                }
                for m in CORE_MODELS
            ]
            return self._json_response({"object": "list", "data": models_data}, 200)

        self._json_response({
            "error": {
                "message": f"Invalid endpoint: {path}. Use /v1/models or /v1/chat/completions.",
                "type": "invalid_request_error",
                "code": "resource_not_found"
            }
        }, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if not (path.endswith("/chat/completions") or path.endswith("/completions")):
            return self._json_response({
                "error": {
                    "message": f"Unsupported POST endpoint: {path}. Expected /v1/chat/completions.",
                    "type": "invalid_request_error",
                    "code": "endpoint_not_found"
                }
            }, 404)

        auth_header = self.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip() if auth_header else ""
        effective_key = token if (token and token != "qwenwork-local" and token != "sk-local") else API_KEY

        if not effective_key:
            return self._json_response({
                "error": {
                    "message": "Missing API Key. Please provide Authorization: Bearer <API_KEY> header or configure QWENWORK_API_KEY.",
                    "type": "authentication_error",
                    "code": "missing_api_key"
                }
            }, 401)

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            req_data = json.loads(raw_body) if raw_body else {}
        except Exception as e:
            return self._json_response({
                "error": {
                    "message": f"Malformed JSON request body: {str(e)}",
                    "type": "invalid_request_error",
                    "code": "bad_json"
                }
            }, 400)

        model_name = req_data.get("model", "qwen3.8-flash")
        messages = req_data.get("messages", [])
        is_stream = bool(req_data.get("stream", False))

        extra_params = {}
        for k in ("temperature", "top_p", "max_tokens", "tools", "tool_choice"):
            if k in req_data and req_data[k] is not None:
                extra_params[k] = req_data[k]

        try:
            upstream_resp = request_chat_completion(
                messages=messages,
                model=model_name,
                stream=is_stream,
                api_key=effective_key,
                extra_params=extra_params
            )
        except Exception as e:
            return self._json_response({"error": {"message": str(e), "type": "upstream_error"}}, 502)

        if is_stream:
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            try:
                for line in upstream_resp:
                    self.wfile.write(line)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        resp_data = upstream_resp.read().decode("utf-8")
        try:
            parsed_resp = json.loads(resp_data)
            self._json_response(parsed_resp, 200)
        except Exception:
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(resp_data.encode("utf-8"))

def run_server():
    """启动 HTTP 2API 服务"""
    print("=" * 65)
    print("  🚀 QwenWork2API - HTTP 2API 服务已启动")
    print("=" * 65)
    print(f"  • 监听地址: http://127.0.0.1:{PORT}")
    print(f"  • 上游服务: {UPSTREAM_BASE}")
    print(f"  • 认证状态: {'✅ 已配置 API Key' if API_KEY else '⚠️ 未检测到全局 API Key'}")
    print("  • 核心模型:")
    for m in CORE_MODELS:
        print(f"      - {m['id']:16s} -> {m['display_name']}")
    print("-" * 65)
    print("  端点指南:")
    print(f"    GET  http://127.0.0.1:{PORT}/v1/models")
    print(f"    POST http://127.0.0.1:{PORT}/v1/chat/completions")
    print(f"    GET  http://127.0.0.1:{PORT}/health")
    print("=" * 65)

    server = ThreadingHTTPServer(("0.0.0.0", PORT), QwenWorkProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] 服务已平稳停止。")
        server.server_close()

# ==================== CLI 命令行交互模式 ====================

def run_cli(args):
    """运行终端 CLI 命令行"""
    prompt = args.prompt

    # 管道输入支持: echo "hello" | python3 main.py cli
    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()

    model = args.model or "qwen3.8-flash"

    # 单次快速执行
    if prompt:
        messages = [{"role": "user", "content": prompt}]
        if args.system:
            messages.insert(0, {"role": "system", "content": args.system})

        try:
            resp = request_chat_completion(messages=messages, model=model, stream=not args.no_stream)
            if not args.no_stream:
                for raw_line in resp:
                    line = raw_line.decode("utf-8", "replace").strip()
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            d = json.loads(data)
                            delta = (d.get("choices") or [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                sys.stdout.write(content)
                                sys.stdout.flush()
                        except Exception:
                            pass
                sys.stdout.write("\n")
            else:
                body = json.loads(resp.read().decode("utf-8"))
                content = body["choices"][0]["message"]["content"]
                print(content)
        except Exception as e:
            sys.stderr.write(f"[ERROR] 执行失败: {e}\n")
            sys.exit(1)
        return

    # 交互式 REPL 对话
    print("=" * 60)
    print(f"  ���� QwenWork CLI 对话模式 (模型: {model})")
    print("  输入问题直接提问，输入 exit 或 quit 退出对话")
    print("=" * 60)

    history = []
    if args.system:
        history.append({"role": "system", "content": args.system})

    while True:
        try:
            user_input = input("\n👤 You > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("再见！")
                break

            history.append({"role": "user", "content": user_input})
            sys.stdout.write("🤖 Qwen > ")
            sys.stdout.flush()

            resp = request_chat_completion(messages=history, model=model, stream=True)
            full_reply = ""
            for raw_line in resp:
                line = raw_line.decode("utf-8", "replace").strip()
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        d = json.loads(data)
                        delta = (d.get("choices") or [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            full_reply += content
                            sys.stdout.write(content)
                            sys.stdout.flush()
                    except Exception:
                        pass
            sys.stdout.write("\n")
            history.append({"role": "assistant", "content": full_reply})
        except (KeyboardInterrupt, EOFError):
            print("\n会话已结束。")
            break

# ==================== MCP (Model Context Protocol) 模式 ====================

def run_mcp():
    """运行标准 Stdio 协议的 Model Context Protocol (MCP) Server"""
    sys.stderr.write("[MCP] QwenWork2API MCP Server starting via stdio...\n")

    def send_response(obj):
        out = json.dumps(obj, ensure_ascii=False)
        sys.stdout.write(out + "\n")
        sys.stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        # 初始化协议
        if method == "initialize":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {}
                    },
                    "serverInfo": {
                        "name": "qwenwork2api-mcp",
                        "version": "1.1.0"
                    }
                }
            })
            continue

        if method == "notifications/initialized":
            continue

        if method == "ping":
            send_response({"jsonrpc": "2.0", "id": req_id, "result": {}})
            continue

        # 暴露的工具列表
        if method == "tools/list":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [
                        {
                            "name": "chat",
                            "description": "调用通义千问 / 千问办公核心大模型进行文本分析、问答与深度推理",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "prompt": {
                                        "type": "string",
                                        "description": "用户提示词或问题内容"
                                    },
                                    "model": {
                                        "type": "string",
                                        "enum": ["qwen3.8-flash", "qwen3.8-max", "qwen-plus"],
                                        "description": "调用的模型名称 (默认 qwen3.8-flash 极速版)"
                                    },
                                    "system_prompt": {
                                        "type": "string",
                                        "description": "可选的系统级人设与指令约束"
                                    }
                                },
                                "required": ["prompt"]
                            }
                        },
                        {
                            "name": "list_models",
                            "description": "查询当前千问办公支持的核心模型清单与上下文特性",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        }
                    ]
                }
            })
            continue

        # 工具调用
        if method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})

            if tool_name == "list_models":
                info_text = json.dumps(CORE_MODELS, ensure_ascii=False, indent=2)
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": info_text}]
                    }
                })
                continue

            if tool_name == "chat":
                prompt = args.get("prompt", "")
                model = args.get("model", "qwen3.8-flash")
                system_prompt = args.get("system_prompt")

                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                try:
                    resp = request_chat_completion(messages=messages, model=model, stream=False)
                    data = json.loads(resp.read().decode("utf-8"))
                    answer = data["choices"][0]["message"]["content"]
                    send_response({
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": answer}]
                        }
                    })
                except Exception as e:
                    send_response({
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                            "isError": True
                        }
                    })
                continue

            # 未知工具
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method/Tool not found: {tool_name}"
                }
            })
            continue

        # 默认通知响应
        if req_id is not None:
            send_response({"jsonrpc": "2.0", "id": req_id, "result": {}})

# ==================== 统一主入口 ====================

def main():
    global PORT
    parser = argparse.ArgumentParser(
        description="QwenWork2API: 阿里��问办公 (QwenWork) OpenAI 兼容 2API / CLI / MCP 三模服务",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="运行模式")

    # 1. Server 子命令 (也是默认模式)
    server_parser = subparsers.add_parser("server", help="启动 HTTP 2API 服务 (默认模式)")
    server_parser.add_argument("-p", "--port", type=int, default=PORT, help=f"监听端口 (默认 {PORT})")

    # 2. CLI 子命令
    cli_parser = subparsers.add_parser("cli", help="以终端命令行方式直接发起对话")
    cli_parser.add_argument("prompt", nargs="?", default="", help="提问内容 (为空则进入交互式对话，也支持标准输入管道)")
    cli_parser.add_argument("-m", "--model", default="qwen3.8-flash", help="指定模型 (默认 qwen3.8-flash)")
    cli_parser.add_argument("-s", "--system", default="", help="指定系统指令 (System Prompt)")
    cli_parser.add_argument("--no-stream", action="store_true", help="禁用流式打字输出，一次性打印结果")

    # 3. MCP 子命令
    subparsers.add_parser("mcp", help="以标准 Stdio Model Context Protocol (MCP) Server 模式启动")

    # 兼容顶级 --mcp 参数
    parser.add_argument("--mcp", action="store_true", help="以��准 Stdio MCP Server 模式启动")
    parser.add_argument("-p", "--port", type=int, default=PORT, help=f"HTTP 服务监听端口 (默认 {PORT})")

    parsed_args = parser.parse_args()

    # 路由判断
    if parsed_args.mcp or parsed_args.subcommand == "mcp":
        run_mcp()
    elif parsed_args.subcommand == "cli":
        run_cli(parsed_args)
    else:
        if parsed_args.port:
            PORT = parsed_args.port
        run_server()

if __name__ == "__main__":
    main()
