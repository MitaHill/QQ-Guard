import os
import json
import re
import threading
import time
import base64
import urllib.parse


class WhiteGroupChecker:
    def __init__(self):
        self.config_file = 'config/white-group.txt'
        self.white_groups = set()
        self.file_timestamp = 0
        self.lock = threading.Lock()
        self.load_groups()
        self.start_file_watcher()

    def load_groups(self):
        """加载白名单群组"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                groups = [line.strip() for line in f if line.strip() and line.strip().isdigit()]
                with self.lock:
                    self.white_groups = set(int(group) for group in groups)
                    self.file_timestamp = os.path.getmtime(self.config_file)
                print(f"加载白名单群组: {len(self.white_groups)} 个")
        except FileNotFoundError:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write('# 白名单群组号，每行一个\n')
            with self.lock:
                self.white_groups = set()
            print("创建白名单群组配置文件")
        except Exception as e:
            print(f"加载白名单群组失败: {e}")
            with self.lock:
                self.white_groups = set()

    def start_file_watcher(self):
        """启动文件监控"""
        def watch_file():
            while True:
                try:
                    if os.path.exists(self.config_file):
                        current_mtime = os.path.getmtime(self.config_file)
                        if current_mtime != self.file_timestamp:
                            print("检测到白名单群组配置变更，重新加载...")
                            self.load_groups()
                except Exception as e:
                    print(f"监控白名单群组配置失败: {e}")
                time.sleep(10)

        threading.Thread(target=watch_file, daemon=True).start()

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

        with self.lock:
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
        with self.lock:
            return int(group_id) in self.white_groups

    def add_group(self, group_id):
        """添加白名单群组"""
        group_id = int(group_id)
        with self.lock:
            self.white_groups.add(group_id)
            self._save_groups()

    def remove_group(self, group_id):
        """移除白名单群组"""
        group_id = int(group_id)
        with self.lock:
            self.white_groups.discard(group_id)
            self._save_groups()

    def _save_groups(self):
        """保存群组配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write('# 白名单群组号，每行一个\n')
                for group in sorted(self.white_groups):
                    f.write(f'{group}\n')
            self.file_timestamp = os.path.getmtime(self.config_file)
            print(f"保存白名单群组配置: {len(self.white_groups)} 个")
        except Exception as e:
            print(f"保存白名单群组配置失败: {e}")

    def get_groups(self):
        """获取所有白名单群组"""
        with self.lock:
            return list(self.white_groups)