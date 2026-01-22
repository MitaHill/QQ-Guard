import json
import os
import re
import urllib.parse

import requests

from src.AppConfig.app_config_store import AppConfigStore


class OneBotHttpClient:
    def __init__(self):
        self.config = self.load_config()
        self.http_url = self.config["http_url"]
        self.ws_url = self.config["ws_url"]
        self.token = self.config["token"]
        self.mode = self.config["mode"]
        self.ws_reconnect_seconds = self.config["ws_reconnect_seconds"]
        self.ws_ping_interval_seconds = self.config["ws_ping_interval_seconds"]
        self.http_post_host = self.config["http_post_host"]
        self.http_post_port = self.config["http_post_port"]
        self.http_post_path = self.config["http_post_path"]
        self.http_post_secret = self.config["http_post_secret"]
        self.headers = {"Content-Type": "application/json"}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
        self.url_patterns = [
            re.compile(r"https?://(?:www\.)?([a-zA-Z0-9.-]+)"),
            re.compile(r"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"),
            re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"),
        ]

    def load_config(self):
        """加载 OneBot API 配置"""
        config = AppConfigStore.get()
        qq_config = config.get("qq_bot_api", {})
        http_post_cfg = qq_config.get("http_post", {}) or {}

        mode = os.getenv("QQ_GUARD_BOT_MODE") or qq_config.get("mode") or "http_post"
        http_url = os.getenv("QQ_GUARD_HTTP_URL") or qq_config.get("http_url") or "http://127.0.0.1:3000"
        http_url = http_url.rstrip("/")
        ws_url = os.getenv("QQ_GUARD_WS_URL") or qq_config.get("ws_url") or ""
        token = os.getenv("QQ_GUARD_TOKEN") or qq_config.get("token") or ""

        http_post_host = os.getenv("QQ_GUARD_HTTP_POST_HOST") or http_post_cfg.get("host") or "0.0.0.0"
        http_post_port = os.getenv("QQ_GUARD_HTTP_POST_PORT") or http_post_cfg.get("port") or 8080
        http_post_path = os.getenv("QQ_GUARD_HTTP_POST_PATH") or http_post_cfg.get("path") or "/"
        http_post_secret = os.getenv("QQ_GUARD_HTTP_POST_SECRET") or http_post_cfg.get("secret") or ""
        if not str(http_post_path).startswith("/"):
            http_post_path = f"/{http_post_path}"

        ws_reconnect_seconds = qq_config.get("ws_reconnect_seconds", 5)
        ws_ping_interval_seconds = qq_config.get("ws_ping_interval_seconds", 30)
        return {
            "http_url": http_url,
            "ws_url": ws_url,
            "token": token,
            "mode": mode,
            "ws_reconnect_seconds": ws_reconnect_seconds,
            "ws_ping_interval_seconds": ws_ping_interval_seconds,
            "http_post_host": http_post_host,
            "http_post_port": _to_int(http_post_port, 8080),
            "http_post_path": http_post_path,
            "http_post_secret": http_post_secret,
        }

    def get_user_info(self, user_id, group_id):
        """获取用户信息"""
        try:
            response = requests.get(
                f"{self.http_url}/get_group_member_info",
                params={"group_id": group_id, "user_id": user_id},
                headers=self.headers,
                timeout=10,
            )
            result = response.json()
            if result.get("status") == "ok":
                return result.get("data", {}).get("nickname", str(user_id))
        except Exception:
            pass
        return str(user_id)

    def get_group_messages(self, group_id, count=20):
        """获取群消息"""
        try:
            response = requests.post(
                f"{self.http_url}/get_group_msg_history",
                headers=self.headers,
                json={"group_id": group_id, "count": count},
                timeout=10,
            )
            result = response.json()
            if result.get("status") == "ok":
                return result.get("data", {}).get("messages", [])
        except Exception as exc:
            print(f"获取群 {group_id} 消息失败: {exc}")
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
                timeout=100,
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
        except Exception:
            return ""

    def extract_json_visible_content(self, json_data):
        """提取JSON消息中用户可见的内容"""
        try:
            data = json.loads(json_data)
            visible_parts = []

            if "prompt" in data:
                prompt = data["prompt"]
                prompt = re.sub(r"\[.*?\]", "", prompt).strip()
                if prompt:
                    visible_parts.append(prompt)

            meta = data.get("meta", {})
            for key, value in meta.items():
                if isinstance(value, dict):
                    if "title" in value and value["title"]:
                        visible_parts.append(value["title"])
                    if "desc" in value and value["desc"]:
                        visible_parts.append(value["desc"])
                    if "host" in value and isinstance(value["host"], dict):
                        nick = value["host"].get("nick", "")
                        if nick:
                            visible_parts.append(nick)

            return " ".join(visible_parts)
        except Exception as exc:
            print(f"解析JSON消息失败: {exc}")
            return json_data

    def parse_message(self, message):
        """解析消息内容"""
        if isinstance(message, str):
            return message
        if isinstance(message, list):
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

            jump_url = meta_contact.get("jumpUrl", "")
            if "uin=" in jump_url:
                match = re.search(r"uin=(\d+)", jump_url)
                if match:
                    return int(match.group(1))

            pc_jump_url = meta_contact.get("pcJumpUrl", "")
            if "groupUin" in pc_jump_url:
                import base64

                match = re.search(r"param=([^&]+)", pc_jump_url)
                if match:
                    try:
                        param = urllib.parse.unquote(match.group(1))
                        decoded = base64.b64decode(param).decode("utf-8")
                        decoded_data = json.loads(decoded)
                        return int(decoded_data.get("groupUin", 0))
                    except Exception:
                        pass
            return None
        except Exception:
            return None

    def send_private_message(self, user_id, message):
        """发送私聊消息"""
        try:
            response = requests.post(
                f"{self.http_url}/send_private_msg",
                headers=self.headers,
                json={"user_id": user_id, "message": message},
                timeout=10,
            )
            return response.json().get("retcode") == 0
        except Exception:
            return False

    def send_group_message(self, group_id, message):
        """发送群消息"""
        try:
            response = requests.post(
                f"{self.http_url}/send_group_msg",
                headers=self.headers,
                json={"group_id": group_id, "message": message},
                timeout=10,
            )
            return response.json().get("retcode") == 0
        except Exception:
            return False

    def delete_message(self, message_id):
        """撤回消息"""
        try:
            response = requests.post(
                f"{self.http_url}/delete_msg",
                headers=self.headers,
                json={"message_id": message_id},
                timeout=10,
            )
            return response.json().get("retcode") == 0
        except Exception:
            return False


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
