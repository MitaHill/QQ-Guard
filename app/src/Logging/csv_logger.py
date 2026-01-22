import csv
import os
import queue
from datetime import datetime

from src.AppConfig.app_config_store import APP_ROOT

class CSVLogger:
    def __init__(self):
        self.log_file = os.path.join(APP_ROOT, 'log', 'chat.csv')
        self.log_queue = queue.Queue()
        self.init_log_file()

    def init_log_file(self):
        """初始化日志文件"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='', encoding='utf-8-sig') as f:
                csv.writer(f).writerow([
                    '时间戳', 'QQ号', 'QQ名', '群号', '消息内容',
                    '是否撤回', '是否白名单', '违规类型', '违规原因', 'AI响应时间(秒)'
                ])

    def log_message(self, user_id, username, group_id, message, is_deleted=False,
                    is_whitelist=False, violation_type="", violation_reason="", response_time=None):
        """记录消息日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = [
            f"'{timestamp}",
            f"'{user_id}",
            username,
            f"'{group_id}",
            message,
            "是" if is_deleted else "否",
            "是" if is_whitelist else "否",
            violation_type,
            violation_reason,
            f"{response_time:.3f}" if response_time else ""
        ]
        self.log_queue.put(log_entry)

    def flush(self):
        """刷新日志到文件"""
        logs = []
        while not self.log_queue.empty():
            try:
                logs.append(self.log_queue.get_nowait())
            except queue.Empty:
                break

        if logs:
            try:
                with open(self.log_file, 'a', newline='', encoding='utf-8-sig') as f:
                    csv.writer(f).writerows(logs)
            except Exception as e:
                print(f"写入CSV日志失败: {e}")
