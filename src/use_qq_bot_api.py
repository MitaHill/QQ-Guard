import requests
import json
import os
import re
import urllib.parse


class QQBotAPI:
    def __init__(self):
        self.config = self.load_config()
        self.http_url = self.config['http_url']
        self.headers = {"Content-Type": "application/json"}
        self.url_patterns = [
            re.compile(r'https?://(?:www\.)?([a-zA-Z0-9.-]+)'),
            re.compile(r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'),
            re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        ]

    def load_config(self):
        """加载QQ机器人API配置"""
        config_file = 'config/qq_bot_api.json'
        default = {"http_url": "http://192.168.9.122:3000"}

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        # 创建默认配置
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=2, ensure_ascii=False)
        return default

    def get_user_info(self, user_id, group_id):
        """获取用户信息"""
        try:
            response = requests.get(
                f"{self.http_url}/get_group_member_info",
                params={"group_id": group_id, "user_id": user_id},
                headers=self.headers,
                timeout=10
            )
            result = response.json()
            if result.get("status") == "ok":
                return result.get("data", {}).get("nickname", str(user_id))
        except:
            pass
        return str(user_id)

    def get_group_messages(self, group_id, count=20):
        """获取群消息"""
        try:
            response = requests.post(
                f"{self.http_url}/get_group_msg_history",
                headers=self.headers,
                json={"group_id": group_id, "count": count},
                timeout=10
            )
            result = response.json()
            if result.get("status") == "ok":
                return result.get("data", {}).get("messages", [])
        except Exception as e:
            print(f"获取群 {group_id} 消息失败: {e}")
        return []

    def extract_forward_content(self, forward_id, depth=1):
        """提取转发消息内容"""
        if depth > 5:
            return ""
        try:
            response = requests.get(
                f"{self.http_url}/get_forward_msg",
                params={"id": forward_id},
                headers=self.headers,
                timeout=100
            )
            result = response.json()
            if result.get("status") != "ok":
                return ""

            all_text = []
            for msg in result.get("data", {}).get("messages", []):
                content = msg.get("content", "")
                text = ""
                if isinstance(content, list):
                    for seg in content:
                        if seg.get("type") == "text":
                            text += seg.get("data", {}).get("text", "")
                        elif seg.get("type") == "forward":
                            text += self.extract_forward_content(
                                seg.get("data", {}).get("id", ""), depth + 1
                            )
                elif isinstance(content, str):
                    text = content
                if text.strip():
                    all_text.append(text.strip())
            return " ".join(all_text)
        except:
            return ""

    def extract_json_visible_content(self, json_data):
        """提取JSON消息中用户可见的内容"""
        try:
            data = json.loads(json_data)
            visible_parts = []

            # 提取prompt（通常是分享的描述文本）
            if "prompt" in data:
                prompt = data["prompt"]
                # 移除[QQ小程序]等标识
                prompt = re.sub(r'\[.*?\]', '', prompt).strip()
                if prompt:
                    visible_parts.append(prompt)

            # 提取meta中的可见内容
            meta = data.get("meta", {})
            for key, value in meta.items():
                if isinstance(value, dict):
                    # 提取title和desc
                    if "title" in value and value["title"]:
                        visible_parts.append(value["title"])
                    if "desc" in value and value["desc"]:
                        visible_parts.append(value["desc"])
                    # 提取nick（分享者昵称）
                    if "host" in value and isinstance(value["host"], dict):
                        nick = value["host"].get("nick", "")
                        if nick:
                            visible_parts.append(nick)

            return " ".join(visible_parts)
        except Exception as e:
            print(f"解析JSON消息失败: {e}")
            # 如果解析失败，返回原始数据（保持向后兼容）
            return json_data

    def parse_message(self, message):
        """解析消息内容"""
        if isinstance(message, str):
            return message
        elif isinstance(message, list):
            text_parts = []
            for seg in message:
                if seg.get("type") == "text":
                    text_parts.append(seg.get("data", {}).get("text", ""))
                elif seg.get("type") == "forward":
                    forward_content = self.extract_forward_content(
                        seg.get("data", {}).get("id", "")
                    )
                    if forward_content:
                        text_parts.append(f"[转发消息: {forward_content}]")
                elif seg.get("type") == "json":
                    json_data = seg.get("data", {}).get("data", "")
                    if json_data:
                        # 只提取用户可见的内容进行检测
                        visible_content = self.extract_json_visible_content(json_data)
                        if visible_content:
                            text_parts.append(f"[分享内容: {visible_content}]")
            return "".join(text_parts)
        return ""

    def extract_domains(self, message):
        """提取消息中的域名"""
        domains = set()
        for pattern in self.url_patterns:
            domains.update(pattern.findall(message))
        return list(domains)

    def extract_group_id_from_json(self, json_data):
        """从群聊分享JSON中提取群号"""
        try:
            data = json.loads(json_data)
            meta_contact = data.get("meta", {}).get("contact", {})

            # 检查jumpUrl
            jump_url = meta_contact.get("jumpUrl", "")
            if "uin=" in jump_url:
                match = re.search(r'uin=(\d+)', jump_url)
                if match:
                    return int(match.group(1))

            # 检查pcJumpUrl
            pc_jump_url = meta_contact.get("pcJumpUrl", "")
            if "groupUin" in pc_jump_url:
                import base64
                match = re.search(r'param=([^&]+)', pc_jump_url)
                if match:
                    try:
                        param = urllib.parse.unquote(match.group(1))
                        decoded = base64.b64decode(param).decode('utf-8')
                        decoded_data = json.loads(decoded)
                        return int(decoded_data.get("groupUin", 0))
                    except:
                        pass
            return None
        except:
            return None

    def send_private_message(self, user_id, message):
        """发送私聊消息"""
        try:
            response = requests.post(
                f"{self.http_url}/send_private_msg",
                headers=self.headers,
                json={"user_id": user_id, "message": message},
                timeout=10
            )
            return response.json().get("retcode") == 0
        except:
            return False

    def send_group_message(self, group_id, message):
        """发送群消息"""
        try:
            response = requests.post(
                f"{self.http_url}/send_group_msg",
                headers=self.headers,
                json={"group_id": group_id, "message": message},
                timeout=10
            )
            return response.json().get("retcode") == 0
        except:
            return False

    def delete_message(self, message_id):
        """撤回消息"""
        try:
            response = requests.post(
                f"{self.http_url}/delete_msg",
                headers=self.headers,
                json={"message_id": message_id},
                timeout=10
            )
            return response.json().get("retcode") == 0
        except:
            return False