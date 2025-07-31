import os
import threading
import time


class WhiteMemberChecker:
    def __init__(self):
        self.config_file = 'config/white-member.txt'
        self.white_members = set()
        self.file_timestamp = 0
        self.lock = threading.Lock()
        self.load_members()
        self.start_file_watcher()

    def load_members(self):
        """加载白名单成员"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                members = [line.strip() for line in f if line.strip() and line.strip().isdigit()]
                with self.lock:
                    self.white_members = set(int(member) for member in members)
                    self.file_timestamp = os.path.getmtime(self.config_file)
                print(f"加载白名单成员: {len(self.white_members)} 个")
        except FileNotFoundError:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write('# 白名单成员QQ号，每行一个\n')
            with self.lock:
                self.white_members = set()
            print("创建白名单成员配置文件")
        except Exception as e:
            print(f"加载白名单成员失败: {e}")
            with self.lock:
                self.white_members = set()

    def start_file_watcher(self):
        """启动文件监控"""
        def watch_file():
            while True:
                try:
                    if os.path.exists(self.config_file):
                        current_mtime = os.path.getmtime(self.config_file)
                        if current_mtime != self.file_timestamp:
                            print("检测到白名单成员配置变更，重新加载...")
                            self.load_members()
                except Exception as e:
                    print(f"监控白名单成员配置失败: {e}")
                time.sleep(10)

        threading.Thread(target=watch_file, daemon=True).start()

    def is_whitelisted(self, user_id):
        """检查用户是否在白名单"""
        with self.lock:
            return int(user_id) in self.white_members

    def add_member(self, user_id):
        """添加白名单成员"""
        user_id = int(user_id)
        with self.lock:
            self.white_members.add(user_id)
            self._save_members()

    def remove_member(self, user_id):
        """移除白名单成员"""
        user_id = int(user_id)
        with self.lock:
            self.white_members.discard(user_id)
            self._save_members()

    def _save_members(self):
        """保存成员配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write('# 白名单成员QQ号，每行一个\n')
                for member in sorted(self.white_members):
                    f.write(f'{member}\n')
            self.file_timestamp = os.path.getmtime(self.config_file)
            print(f"保存白名单成员配置: {len(self.white_members)} 个")
        except Exception as e:
            print(f"保存白名单成员配置失败: {e}")

    def get_members(self):
        """获取所有白名单成员"""
        with self.lock:
            return list(self.white_members)