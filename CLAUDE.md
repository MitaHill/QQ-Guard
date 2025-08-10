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