# QQ-Guard

基于 LLoneBot 框架的 QQ 群聊敏感词检测机器人，使用 AI 智能识别并自动撤回违规消息。

## 🌟 特性

- **智能检测** - 集成硅基流动 AI 模型，准确识别敏感内容
- **多重过滤** - 黑名单词库 + 网站白名单 + 群聊分享检测
- **实时撤回** - 自动撤回违规消息并通知管理员
- **统计排行** - 生成违规用户排行榜，定时推送
- **白名单机制** - 支持用户和群组白名单
- **日志记录** - 完整的操作日志和 CSV 数据导出


## 修改内容

将`info2ai`的调用方式从`flask`改为函数直接调用，并把`info2ai/`移动到`src/`目录中。


将原本的`info2ai/conversation_history.json`移动到`config/info2ai/conversation_history.json`


将原本的`info2ai/info2ai-config.json`移动到`config/info2ai/base-config.json`


将原本的`info2ai/prompt-files/`移动到`config/info2ai/prompt-files/`


将原本的`info2ai/prompt.txt`移动到`config/info2ai/prompt.txt`


## 更新反馈


2025-08-10 22:53


运行良好。

接下来请增加一个功能

### 聊天功能


请查询`LLoneBot`的API部分，并增加
- `src/chat/`目录，作为模块的源目录。
- `config/chat2ai/`目录，作为模块的配置目录，有模型的提示词、语料库、API设置。

#### 具体功能
- 当被`@`时，例如，这个机器人的名字叫做`加纳~`，有人发送了消息`@加纳~ 你在干什么呀`，则将此消息发送到模型处。
- 设置`10%`的概率根据群聊中的上下文聊上几句，这个概率可以在`config/chat2ai/base-config.json`中设置。
- 
- 值得注意的地方：调用方式和`info2ai`一样函数直接调用，且也有
  - `config/chat2ai/prompt-files/` 聊天模型语料库
  - `config/chat2ai/base-config.json` 聊天模型基础设置
  - `config/chat2ai/conversation_history.json` 上下文记忆数据
  - `config/chat2ai/prompt.txt` 聊天提示词
- 但不同的是，增加了以下文件
  - `config/chat2ai/chat-group.txt` 可以进行聊天的群聊，只有在此群聊，聊天机器人才会激活。
  - `config/chat2ai/chat-histroy/(QQ-Group-Number)/conversation_history.json`每个QQ群的上下文记录。例如`config/chat2ai/chat-histroy/1234567890/conversation_history.json`。

## SOP

修改完 -> 提交 -> 测试 -> 若有问题回到开始，若无问题则同步远程仓库一次。

## 当前约定与参数（覆盖历史记录）

- **分支**: 本次大改使用 `big-change` 分支。
- **目录结构**:
  - `app/`：应用源码与配置
  - `docker/`：镜像构建文件
  - `pre-run/`：运行环境（docker-compose + 持久化）
  - `example-run/`：模板文件（供复制使用）
  - `app/WebUI/`：Vite + Vue 前端
- **配置合并**: 所有配置合并到 `app/config/AppConfig.Yaml`，黑名单/白名单/群列表直接内嵌为 YAML 列表。
- **环境变量**:
  - `OPENAI_API_KEY`：OpenAI API Key（默认读取该变量）
  - `INFO2AI_API_KEY`：兼容旧环境的备用 Key
  - `QQ_GUARD_AI_PROVIDER`：`openai` 或 `ollama`
  - `INFO2AI_PROMPT_DIR`：提示词语料目录
  - `INFO2AI_PROMPT_FILE`：主提示词文件
  - `QQ_GUARD_BOT_MODE`：`http_post` 或 `websocket`
  - `QQ_GUARD_HTTP_URL` / `QQ_GUARD_WS_URL` / `QQ_GUARD_TOKEN`
  - `QQ_GUARD_HTTP_POST_HOST` / `QQ_GUARD_HTTP_POST_PORT` / `QQ_GUARD_HTTP_POST_PATH` / `QQ_GUARD_HTTP_POST_SECRET`
  - `QQ_GUARD_WEB_HOST` / `QQ_GUARD_WEB_PORT` / `QQ_GUARD_WEB_CORS_ORIGINS`
  - 示例位置：`example-run/.env`（脱敏示例），真实配置位于 `pre-run/.env`。
- **Info2AI**:
  - 提示词与语料路径必须来自环境变量，不再允许硬编码或相对路径。
  - 对话历史使用 SQLite：`app/db/all.db`，表名 `conversation_history`。
- **日志与数据**:
  - 运行日志在 `app/log/`，数据库在 `app/db/`。
  - `app/log/`、`app/db/`、`pre-run/.env`、`pre-run/log/`、`pre-run/db/` 已加入 `.gitignore`，禁止入库。
  - 聊天记录表：`chat_messages`（位于 `app/db/all.db`）。
- **Docker 部署**:
  - 基础镜像：`docker/base/Dockerfile`（内含 Python 环境与依赖）。
  - 应用镜像：`docker/app/Dockerfile`。
  - 部署与发布统一使用 `pre-run/docker-compose.yaml`。
  - Web 控制台服务：`web`（Flask API），前端开发服务：`web-ui`（Vite + Vue）。
- **NapCat / OneBot 11**:
  - `qq_bot_api.mode`：`http_post` 或 `websocket`。
  - `qq_bot_api.ws_url`：正向 WebSocket 地址。
  - `qq_bot_api.token`：鉴权密钥（以 `Authorization: Bearer <token>` 发送）。
  - `qq_bot_api.ws_reconnect_seconds` / `qq_bot_api.ws_ping_interval_seconds`：WS 重连与心跳配置。
  - `qq_bot_api.http_post`：HTTP 上报监听配置（支持 `secret` 校验 `X-Signature`）。
- **AI 供应商**:
  - `info2ai.provider`：`openai` 或 `ollama`（可用 `QQ_GUARD_AI_PROVIDER` 覆盖）。
  - `info2ai.openai.api_base_url` / `model_name` / `api_key_env`。
  - `info2ai.ollama.base_url` / `model_name` / `thinking_enabled`（Ollama 无鉴权）。
  - `QQ_GUARD_OLLAMA_THINKING`：可选，覆盖 `thinking_enabled`。
- **源码结构规则**:
  - `app/src/` 允许并推荐使用二级模块子目录。
  - 子目录命名规则：大驼峰命名法（如 `AppConfig`, `AiCore`, `PolicyRules`）。
  - 现有分类：`AppConfig`, `AiCore`, `BotApi`, `DataStore`, `Logging`, `MessageHandling`, `Monitoring`, `PolicyRules`, `Reporting`, `TaskQueue`, `WebUi`。
