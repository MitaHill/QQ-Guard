# QQ-Guard

基于 LLoneBot 框架的 QQ 群聊敏感词检测机器人，使用 AI 智能识别并自动撤回违规消息。

## 🌟 特性

- **智能检测** - 集成硅基流动 AI 模型，准确识别敏感内容
- **多重过滤** - 黑名单词库 + 网站白名单 + 群聊分享检测
- **实时撤回** - 自动撤回违规消息并通知管理员
- **统计排行** - 生成违规用户排行榜，定时推送
- **白名单机制** - 支持用户和群组白名单
- **日志记录** - 完整的操作日志和 CSV 数据导出

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 安装了`Git`程序，或者打包项目下载也可以
- LLoneBot (QQ 机器人框架) 不设置token，最好使用`docker`部署
- 硅基流动API账号，或兼容OpenAI-API

### 安装部署

1. **克隆项目**
```bash
git clone https://github.com/yourusername/QQ-Guard.git
cd QQ-Guard
```

2. **安装依赖**
```bash
pip install requests flask pillow
```

3. **配置文件设置**

- 配置 QQ 机器人 API `/config/qq_bot_api.json`

```
{
  "http_url": "http://192.168.9.122:3000"
}
```


- 配置监控群组 `config/monitor-groups.txt`

  QQ号码，一行一个


#### 注意

配置QQ机器人API部分，需要你自行部署LLoneBot，并将API地址配置到`config/qq_bot_api.json`中

---

4. **配置 AI 服务**  编辑`info2ai/info2ai-config.json`
```bash
{
  "api_base_url": "https://api.siliconflow.cn/v1",
  "api_key": "API密钥填入这里",
  "model_name": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
  "knowledge_dir": "prompt-files",
  "prompt_file": "prompt.txt",
  "max_history": 30
}
```

建议模型选择`deepseek-ai/DeepSeek-R1-0528-Qwen3-8B`

当然更大的模型更好

不过硅基流动的API 10B以下模型才免费调用

因此选择此模型是不错的选择



5. **启动服务**
```bash
python main.py
```

## 📁 项目结构

```
QQ-Guard/
├── main.py                    # 主程序入口
├── src/                       # 核心模块
│   ├── use_qq_bot_api.py     # QQ Bot API 接口
│   ├── use_info2ai_api.py    # AI 检测 API
│   ├── draw_top.py           # 排行榜生成
│   ├── black_rules.py        # 黑名单规则
│   ├── white_*.py            # 白名单检查
│   └── queue.py              # AI 检测队列
├── config/                    # 配置文件
│   ├── qq_bot_api.json       # QQ API 配置
│   ├── ctl-list.txt          # 管理员列表
│   ├── monitor-groups.txt    # 监控群组
│   ├── black-rules.txt       # 黑名单规则
│   └── website-white.txt     # 网站白名单
├── info2ai/                   # AI 服务
│   ├── app.py                # AI 服务器
│   ├── prompt.txt            # AI 提示词
│   └── prompt-files/         # 知识库文件
└── log/                       # 日志文件
```

## ⚙️ 配置说明

### QQ Bot API 配置
```json
{
    "http_url": "http://127.0.0.1:3000",
    "access_token": "your_access_token"
}
```

### AI 模型配置
```json
{
    "api_key": "your_api_key",
    "model": "deepseek-chat",
    "base_url": "https://api.siliconflow.cn/v1"
}
```

### 黑名单规则示例
```
# 支持正则表达式
政治敏感词.*
.*博彩.*
开盒|人肉
```

## 📊 功能模块

### 检测流程
1. **白名单过滤** - 跳过白名单用户和群组
2. **规则检测** - 黑名单词库、网站检测、群聊分享
3. **AI 智能检测** - 深度语义分析
4. **消息撤回** - 自动撤回违规内容
5. **统计记录** - 记录违规数据

### 管理功能
- 实时违规通知
- 定时排行榜推送
- 完整操作日志
- CSV 数据导出

## 📝 使用说明

### 添加管理员
在 `config/ctl-list.txt` 中添加 QQ 号：
```
123456789
987654321
```

### 配置监控群组
在 `config/monitor-groups.txt` 中添加群号：
```
1234567890
9876543210
```

### 自定义规则
编辑 `config/black-rules.txt` 添加检测规则：
```
违规词1
违规词2.*
.*正则表达式.*
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [LLoneBot](https://github.com/LLOneBot/LLOneBot) - QQ 机器人框架
- [硅基流动](https://cloud.siliconflow.cn/) - AI 模型服务
- 所有贡献者和用户的支持

## ⚠️ 免责声明

本项目仅供学习和研究使用，请遵守相关法律法规和平台服务条款。使用本项目所产生的任何后果，由使用者自行承担。

---

<div align="center">
如果这个项目对你有帮助，请给个 ⭐️ Star 支持一下！
</div>
