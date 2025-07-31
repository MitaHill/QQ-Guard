import os
import threading
import time


class MonitorGroups:
    def __init__(self):
        self.config_file = 'config/monitor-groups.txt'
        self.groups = []
        self.file_timestamp = 0
        self.lock = threading.Lock()
        self.load_groups()
        self.start_file_watcher()

    def load_groups(self):
        """加载监控群组列表"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                groups = [line.strip() for line in f if line.strip() and line.strip().isdigit()]
                with self.lock:
                    self.groups = [int(group) for group in groups]
                    self.file_timestamp = os.path.getmtime(self.config_file)
                print(f"加载监控群组: {self.groups}")
        except FileNotFoundError:
            # 创建默认配置
            default_group = [1051352466]
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(map(str, default_group)))
            with self.lock:
                self.groups = default_group
            print(f"创建默认监控群组配置: {default_group}")
        except Exception as e:
            print(f"加载监控群组失败: {e}")
            with self.lock:
                self.groups = [1051352466]  # 默认群组

    def start_file_watcher(self):
        """启动文件监控"""
        def watch_file():
            while True:
                try:
                    if os.path.exists(self.config_file):
                        current_mtime = os.path.getmtime(self.config_file)
                        if current_mtime != self.file_timestamp:
                            print("检测到监控群组配置文件变更，重新加载...")
                            self.load_groups()
                except Exception as e:
                    print(f"监控配置文件变更检测失败: {e}")
                time.sleep(10)

        threading.Thread(target=watch_file, daemon=True).start()

    def get_groups(self):
        """获取监控群组列表"""
        with self.lock:
            return self.groups.copy()

    def add_group(self, group_id):
        """添加监控群组"""
        group_id = int(group_id)
        with self.lock:
            if group_id not in self.groups:
                self.groups.append(group_id)
                self._save_groups()

    def remove_group(self, group_id):
        """移除监控群组"""
        group_id = int(group_id)
        with self.lock:
            if group_id in self.groups:
                self.groups.remove(group_id)
                self._save_groups()

    def _save_groups(self):
        """保存群组配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(map(str, self.groups)))
            self.file_timestamp = os.path.getmtime(self.config_file)
            print(f"保存监控群组配置: {self.groups}")
        except Exception as e:
            print(f"保存监控群组配置失败: {e}")

    def is_monitored(self, group_id):
        """检查群组是否被监控"""
        with self.lock:
            return int(group_id) in self.groups