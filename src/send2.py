import os
import threading
import time


class AdminNotifier:
    def __init__(self, message_sender):
        self.config_file = 'config/ctl-list.txt'
        self.sender = message_sender
        self.admins = []
        self.file_timestamp = 0
        self.lock = threading.Lock()
        self.load_admins()
        self.start_file_watcher()

    def load_admins(self):
        """加载管理员列表"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                admins = [line.strip() for line in f if line.strip() and line.strip().isdigit()]
                with self.lock:
                    self.admins = [int(admin) for admin in admins]
                    self.file_timestamp = os.path.getmtime(self.config_file)
                print(f"加载管理员列表: {len(self.admins)} 个")
        except FileNotFoundError:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write('# 管理员QQ号，每行一个\n')
            with self.lock:
                self.admins = []
            print("创建管理员配置文件")
        except Exception as e:
            print(f"加载管理员列表失败: {e}")
            with self.lock:
                self.admins = []

    def start_file_watcher(self):
        """启动文件监控"""

        def watch_file():
            while True:
                try:
                    if os.path.exists(self.config_file):
                        current_mtime = os.path.getmtime(self.config_file)
                        if current_mtime != self.file_timestamp:
                            print("检测到管理员配置变更，重新加载...")
                            self.load_admins()
                except Exception as e:
                    print(f"监控管理员配置失败: {e}")
                time.sleep(10)

        threading.Thread(target=watch_file, daemon=True).start()

    def notify_violation(self, user_id, group_id, action):
        """通知管理员违规消息"""
        message = f"{user_id} 已被{action}消息在群号 {group_id} 中"
        with self.lock:
            admin_list = self.admins.copy()

        for admin_id in admin_list:
            try:
                self.sender.send_private_message(admin_id, message)
            except Exception as e:
                print(f"发送通知给管理员 {admin_id} 失败: {e}")

    def send_ranking(self, ranking_text):
        """发送排行榜给管理员"""
        print(f"[AdminNotifier] 开始发送文字排行榜...")

        with self.lock:
            admin_list = self.admins.copy()

        if not admin_list:
            print("[AdminNotifier] 错误: 没有配置管理员")
            return

        for admin_id in admin_list:
            try:
                result = self.sender.send_private_message(admin_id, ranking_text)
                print(f"[AdminNotifier] 发送给管理员 {admin_id}: {result}")
            except Exception as e:
                print(f"[AdminNotifier] 发送给管理员 {admin_id} 失败: {e}")

    def get_admins(self):
        """获取管理员列表"""
        with self.lock:
            return self.admins.copy()

    def add_admin(self, admin_id):
        """添加管理员"""
        admin_id = int(admin_id)
        with self.lock:
            if admin_id not in self.admins:
                self.admins.append(admin_id)
                self._save_admins()

    def remove_admin(self, admin_id):
        """移除管理员"""
        admin_id = int(admin_id)
        with self.lock:
            if admin_id in self.admins:
                self.admins.remove(admin_id)
                self._save_admins()

    def _save_admins(self):
        """保存管理员配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write('# 管理员QQ号，每行一个\n')
                for admin in self.admins:
                    f.write(f'{admin}\n')
            self.file_timestamp = os.path.getmtime(self.config_file)
            print(f"保存管理员配置: {len(self.admins)} 个")
        except Exception as e:
            print(f"保存管理员配置失败: {e}")