# QQ-Guard

基于 LLoneBot 框架的 QQ 群聊敏感词检测机器人，使用 AI 智能识别并自动撤回违规消息。

## 🌟 特性

- **智能检测** - 集成硅基流动 AI 模型，准确识别敏感内容
- **多重过滤** - 黑名单词库 + 网站白名单 + 群聊分享检测
- **实时撤回** - 自动撤回违规消息并通知管理员
- **统计排行** - 生成违规用户排行榜，定时推送
- **白名单机制** - 支持用户和群组白名单
- **日志记录** - 完整的操作日志和 CSV 数据导出

## 📁 目录结构

```
QQ-Guard/
├── app/                  # 应用源码与配置
│   ├── main.py
│   ├── src/              # 推荐驼峰命名的二级模块目录
│   │   ├── AppConfig/
│   │   ├── AiCore/
│   │   ├── BotApi/
│   │   ├── DataStore/
│   │   ├── Logging/
│   │   ├── MessageHandling/
│   │   ├── Monitoring/
│   │   ├── PolicyRules/
│   │   ├── Reporting/
│   │   ├── TaskQueue/
│   │   └── WebUi/
│   ├── WebUI/            # Vite + Vue 前端
│   ├── config/
│   │   ├── AppConfig.Yaml
│   │   └── info2ai/
│   │       ├── prompt.txt
│   │       └── prompt-files/
│   └── requirements.txt
├── docker/               # 镜像构建文件
│   ├── base/Dockerfile
│   └── app/Dockerfile
├── pre-run/              # 运行环境（本地持久化）
│   ├── docker-compose.yaml
│   ├── .env
│   ├── db/
│   └── log/
├── example-run/          # 模板文件（请复制使用）
├── PROJECT.MD
└── README.md
```

## ⚙️ 配置说明

### AppConfig.Yaml
核心配置统一收敛在 `app/config/AppConfig.Yaml`，包括：
- 机器人 API 地址
- NapCat / OneBot 11 通讯模式与鉴权
- 监控群、白名单群/用户、管理员
- 黑名单规则、网站白名单
- Info2AI 模型配置参数

#### AI 供应商
- `info2ai.provider`：`openai` 或 `ollama`
- `info2ai.openai.api_base_url`：OpenAI 兼容 API 地址（可替换为第三方兼容服务）
- `info2ai.openai.model_name`：OpenAI 模型名
- `info2ai.ollama.base_url`：Ollama API 基址（默认 `http://127.0.0.1:11434`）
- `info2ai.ollama.model_name`：Ollama 模型名
- `info2ai.ollama.thinking_enabled`：是否开启思考输出（返回 `<think>...</think>` 内容）

#### NapCat / OneBot 11 配置要点
- `qq_bot_api.mode`：`http_post`（HTTP 事件上报）或 `websocket`（WebSocket 事件推送）。
- `qq_bot_api.http_url`：HTTP API 地址（用于发消息、撤回等操作）。
- `qq_bot_api.ws_url`：WebSocket 服务端地址（正向 WS），用于接收事件。
- `qq_bot_api.token`：鉴权密钥（与 NapCat 配置中的 `token` 一致）。
- `qq_bot_api.ws_reconnect_seconds`：断线重连间隔（秒）。
- `qq_bot_api.ws_ping_interval_seconds`：WS 心跳间隔（秒）。
- `qq_bot_api.http_post`：HTTP 上报服务器监听配置（`host`/`port`/`path`/`secret`）。

说明：
- 当 NapCat 配置了 `token`，本项目会通过 `Authorization: Bearer <token>` 发送请求（符合 OneBot 11 鉴权规范）。
- 当使用 HTTP 上报模式时，可在 NapCat 的 `http_post.secret` 中设置签名密钥，本项目会校验 `X-Signature`（HMAC SHA1）。
- HTTP 上报模式需将 NapCat 的 `http_post.url` 指向本服务（如 `http://<host>:<port>/`）。

### 环境变量
请在 `pre-run/.env` 设置以下变量：

- `OPENAI_API_KEY`：OpenAI API Key（可指向兼容服务）
- `INFO2AI_API_KEY`：兼容旧环境的备用 Key
- `INFO2AI_PROMPT_DIR`：提示词语料目录（默认 `/app/config/info2ai/prompt-files`）
- `INFO2AI_PROMPT_FILE`：主提示词文件（默认 `/app/config/info2ai/prompt.txt`）
- `QQ_GUARD_AI_PROVIDER`：`openai` 或 `ollama`
- `OPENAI_API_KEY`：OpenAI API Key（默认读取该变量，若缺失会尝试 `INFO2AI_API_KEY`）
- `QQ_GUARD_OLLAMA_THINKING`：可选，覆盖 `info2ai.ollama.thinking_enabled`
- `QQ_GUARD_BOT_MODE`：`http_post` 或 `websocket`
- `QQ_GUARD_HTTP_URL`：HTTP API 地址
- `QQ_GUARD_WS_URL`：WebSocket 地址
- `QQ_GUARD_TOKEN`：OneBot 鉴权 token
- `QQ_GUARD_HTTP_POST_HOST`：HTTP 上报监听地址
- `QQ_GUARD_HTTP_POST_PORT`：HTTP 上报监听端口
- `QQ_GUARD_HTTP_POST_PATH`：HTTP 上报路径
- `QQ_GUARD_HTTP_POST_SECRET`：HTTP 上报签名密钥
- `QQ_GUARD_WEB_HOST`：Web 控制台监听地址
- `QQ_GUARD_WEB_PORT`：Web 控制台端口
- `QQ_GUARD_WEB_CORS_ORIGINS`：前端开发服务器的允许来源（逗号分隔）

## 💾 数据持久化

- SQLite: `app/db/all.db`（表 `conversation_history`, `chat_messages`）
- 运行日志: `app/log/`

通过 `pre-run/docker-compose.yaml` 已挂载为持久化目录。

## 🐳 测试 / 构建 / 发布（Docker Compose）

全部流程基于 Docker Compose 执行。

### 构建基础镜像
```bash
cd pre-run
docker compose --profile build build base
```

### 构建应用镜像
```bash
docker compose build app
```

### 运行（测试/发布）
```bash
docker compose up -d
docker compose logs -f app
```

### Web 控制台（Flask API）
```bash
docker compose up -d web
docker compose logs -f web
```

### Web 前端（Vite + Vue，开发模式）
```bash
docker compose --profile frontend up -d web-ui
```

### 停止
```bash
docker compose down
```

## 🧪 本地开发（可选）

推荐优先使用 Docker Compose。若需本地运行，请使用虚拟环境避免污染系统环境：

```bash
cd app
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
python -m src.WebUi.web_ui_app
```

前端开发：

```bash
cd app/WebUI
npm install
npm run dev
```

如需自定义前端 API 代理地址，可设置环境变量 `VITE_API_TARGET`。

## 📌 说明

- `example-run/` 提供模板文件，请复制到 `pre-run/` 使用并填入实际参数。
- `.env` 与运行时数据目录已加入 `.gitignore`，避免敏感数据入库。
- HTTP 上报模式需要暴露端口，`docker-compose.yaml` 已默认映射 `QQ_GUARD_HTTP_POST_PORT`。
- Web 控制台默认端口为 `QQ_GUARD_WEB_PORT`（默认 5000），前端开发服务器默认端口 5173。
