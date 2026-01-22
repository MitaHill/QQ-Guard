import json
import re
import base64
import urllib.parse

from src.AppConfig.app_config_store import AppConfigStore


class WhiteGroupChecker:
    def __init__(self):
        self.white_groups = set()
        self._config_version = -1
        self.load_groups()

    def load_groups(self):
        """加载白名单群组"""
        config = AppConfigStore.get()
        groups = config.get("white_groups", [])
        self.white_groups = set(int(group) for group in groups if str(group).isdigit())
        self._config_version = AppConfigStore.version()
        print(f"加载白名单群组: {len(self.white_groups)} 个")

    def _ensure_latest(self):
        AppConfigStore.get()
        if AppConfigStore.version() != self._config_version:
            self.load_groups()

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

    def check_group_share_whitelist(self, json_data):
        """检查群聊分享是否在白名单"""
        shared_group_id = self.extract_group_id_from_json(json_data)
        if shared_group_id is None:
            return False, None

        self._ensure_latest()
        is_whitelisted = shared_group_id in self.white_groups

        return is_whitelisted, shared_group_id

    def check_group_share(self, message):
        """检查是否为群聊分享消息并验证白名单"""
        if isinstance(message, list):
            for seg in message:
                if seg.get("type") == "json":
                    json_data = seg.get("data", {}).get("data", "")
                    if json_data and "推荐群聊" in json_data:
                        is_whitelisted, shared_group_id = self.check_group_share_whitelist(json_data)
                        return True, is_whitelisted, shared_group_id
        return False, True, None

    def is_whitelisted(self, group_id):
        """检查群组是否在白名单"""
        self._ensure_latest()
        return int(group_id) in self.white_groups

    def add_group(self, group_id):
        """添加白名单群组"""
        group_id = int(group_id)
        self._ensure_latest()
        self.white_groups.add(group_id)
        self._save_groups()

    def remove_group(self, group_id):
        """移除白名单群组"""
        group_id = int(group_id)
        self._ensure_latest()
        self.white_groups.discard(group_id)
        self._save_groups()

    def _save_groups(self):
        """保存群组配置到文件"""
        config = AppConfigStore.get()
        config["white_groups"] = sorted(self.white_groups)
        AppConfigStore.save(config)
        self._config_version = AppConfigStore.version()
        print(f"保存白名单群组配置: {len(self.white_groups)} 个")

    def get_groups(self):
        """获取所有白名单群组"""
        self._ensure_latest()
        return list(self.white_groups)
