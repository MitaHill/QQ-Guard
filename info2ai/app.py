import requests
import json
import os
import re
import glob
from typing import Optional
from flask import Flask, jsonify


class SiliconFlowClient:
    def __init__(self):
        self.config = self.load_config()
        self.base_url = self.config.get('api_base_url', 'https://api.siliconflow.cn/v1')
        self.api_key = self.config.get('api_key', 'sk-dpnpbtqxfmkjhhpkyxjgdkdtmqtvccbirokialfkbuullmsy')
        self.model = self.config.get('model_name', 'deepseek-ai/DeepSeek-R1-0528-Qwen3-8B')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.full_prompt = ""
        self.cache_file = "conversation_history.json"
        self.history = []
        self.max_history = self.config['max_history']

    def load_config(self):
        """加载配置文件"""
        config_file = "info2ai-config.json"
        default_config = {
            "api_base_url": "https://api.siliconflow.cn/v1",
            "api_key": "sk-dpnpbtqxfmkjhhpkyxjgdkdtmqtvccbirokialfkbuullmsy",
            "model_name": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            "knowledge_dir": "prompt-files",
            "prompt_file": "prompt.txt",
            "max_history": 30
        }

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except:
                pass

        # 创建默认配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        print(f"已创建配置文件: {config_file}")
        return default_config

    def load_knowledge_base(self):
        """加载知识库和提示词"""
        knowledge_content = ""

        # 读取知识库文件
        knowledge_dir = self.config['knowledge_dir']
        if os.path.exists(knowledge_dir):
            txt_files = glob.glob(os.path.join(knowledge_dir, "*.txt"))
            for file_path in txt_files:
                filename = os.path.basename(file_path)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        knowledge_content += f"{filename}的内容\n{content}\n\n"
                        print(f"加载知识库: {filename}")
                except Exception as e:
                    print(f"读取文件失败 {filename}: {e}")

        # 读取主提示词
        main_prompt = ""
        prompt_file = self.config['prompt_file']
        if os.path.exists(prompt_file):
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    main_prompt = f.read().strip()
                    print(f"加载主提示词: {prompt_file}")
            except Exception as e:
                print(f"读取提示词失败: {e}")

        # 拼接完整提示词
        self.full_prompt = knowledge_content + main_prompt
        print(f"知识库拼接完成，总长度: {len(self.full_prompt)} 字符")

    def load_history(self):
        """加载对话历史"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f).get('history', [])
            except:
                self.history = []

    def save_history(self):
        """保存对话历史"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump({'history': self.history}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史失败: {e}")

    def _truncate_history(self):
        """截断历史记录，保留第一轮+最近对话"""
        if len(self.history) <= self.max_history:
            return

        # 保留第一轮对话
        first_round = self.history[0] if self.history else None
        recent_rounds = self.history[-(self.max_history - 1):]

        self.history = [first_round] + recent_rounds if first_round else recent_rounds

    def chat(self, message: str) -> Optional[str]:
        """与硅基流动API对话"""
        # 构建messages格式的对话历史
        messages = [{"role": "system", "content": self.full_prompt}]

        # 添加历史对话
        for msg in self.history[-10:]:
            if isinstance(msg, dict) and 'user' in msg and 'assistant' in msg:
                messages.append({"role": "user", "content": msg['user']})
                messages.append({"role": "assistant", "content": msg['assistant']})

        # 添加当前消息
        messages.append({"role": "user", "content": message})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": False
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=600
            )

            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()

                # 保存对话历史
                self.history.append({
                    'user': message,
                    'assistant': ai_response
                })
                self._truncate_history()
                self.save_history()

                return ai_response
            else:
                print(f"硅基流动API错误: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"请求错误: {e}")

        return None

    def judge(self, content: str) -> bool:
        """判断内容是否违规"""
        response = self.chat(content)
        if not response:
            return False

        # 提取布尔值
        match = re.search(r'```\s*(true|false)\s*```', response, re.IGNORECASE)
        return match.group(1).lower() == 'true' if match else False


# 全局客户端
siliconflow_client = None


def init_siliconflow():
    """初始化硅基流动客户端"""
    global siliconflow_client

    siliconflow_client = SiliconFlowClient()

    print("加载知识库和提示词...")
    siliconflow_client.load_knowledge_base()
    siliconflow_client.load_history()

    # 预热对话
    print("预热模型...")
    response = siliconflow_client.chat("ready")
    if response:
        print("✅ 模型预热完成")
        return True

    print("❌ 模型预热失败")
    return False


# Flask应用
app = Flask(__name__)


@app.route('/info2ai/api/<path:content>')
def judge_content(content):
    """判断内容API"""
    global siliconflow_client

    if not siliconflow_client:
        return jsonify(False)

    try:
        result = siliconflow_client.judge(content)
        return jsonify(result)
    except Exception as e:
        print(f"API错误: {e}")
        return jsonify(False)


if __name__ == "__main__":
    print("初始化硅基流动AI系统...")
    if init_siliconflow():
        print("🚀 启动Flask API服务器 (端口7000)")
        app.run(host='127.0.0.1', port=7000, debug=False)
    else:
        print("❌ 系统初始化失败")