import os
import logging
from datetime import datetime


class SystemLogger:
    def __init__(self):
        self.log_file = 'log/sys.log'
        self.max_size = 50 * 1024 * 1024  # 50MB
        self.init_logger()

    def init_logger(self):
        """初始化系统日志"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        # 检查并清理日志文件
        self._trim_log_if_needed()

        # 配置日志格式
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _trim_log_if_needed(self):
        """检查日志大小并清理"""
        if not os.path.exists(self.log_file):
            return

        if os.path.getsize(self.log_file) > self.max_size:
            self._trim_log()

    def _trim_log(self):
        """保留最新日志，删除旧日志直到小于50MB"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 从末尾开始保留行，直到大小小于50MB
            kept_lines = []
            current_size = 0

            for line in reversed(lines):
                line_size = len(line.encode('utf-8'))
                if current_size + line_size < self.max_size:
                    kept_lines.append(line)
                    current_size += line_size
                else:
                    break

            # 反转回正确顺序并写入
            kept_lines.reverse()
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.writelines(kept_lines)

        except Exception as e:
            print(f"清理日志文件失败: {e}")

    def info(self, message):
        """记录信息日志"""
        self.logger.info(message)
        self._check_size_after_write()

    def error(self, message):
        """记录错误日志"""
        self.logger.error(message)
        self._check_size_after_write()

    def warning(self, message):
        """记录警告日志"""
        self.logger.warning(message)
        self._check_size_after_write()

    def debug(self, message):
        """记录调试日志"""
        self.logger.debug(message)
        self._check_size_after_write()

    def _check_size_after_write(self):
        """写入后检查文件大小"""
        try:
            if os.path.exists(self.log_file) and os.path.getsize(self.log_file) > self.max_size:
                # 重新初始化logger以避免文件锁定
                for handler in self.logger.handlers[:]:
                    if isinstance(handler, logging.FileHandler):
                        handler.close()
                        self.logger.removeHandler(handler)

                self._trim_log()

                # 重新添加文件handler
                file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
                file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
                self.logger.addHandler(file_handler)
        except:
            pass