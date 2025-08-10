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
