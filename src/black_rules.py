import os
import threading
import time


class BlackRulesChecker:
    def __init__(self):
        self.config_file = 'config/black-rules.txt'
        self.black_rules = []
        self.file_timestamp = 0
        self.lock = threading.Lock()
        self.load_rules()
        self.start_file_watcher()

    def load_rules(self):
        """加载黑名单规则"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                rules = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                with self.lock:
                    self.black_rules = rules
                    self.file_timestamp = os.path.getmtime(self.config_file)
                print(f"加载黑名单规则: {len(self.black_rules)} 条")
        except FileNotFoundError:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write('# 黑名单关键词规则，每行一个\n')
                f.write('# 支持完整匹配\n')
                f.write('赌博\n')
                f.write('诈骗\n')
            with self.lock:
                self.black_rules = ['赌博', '诈骗']
            print("创建黑名单规则配置文件")
        except Exception as e:
            print(f"加载黑名单规则失败: {e}")
            with self.lock:
                self.black_rules = []

    def start_file_watcher(self):
        """启动文件监控"""
        def watch_file():
            while True:
                try:
                    if os.path.exists(self.config_file):
                        current_mtime = os.path.getmtime(self.config_file)
                        if current_mtime != self.file_timestamp:
                            print("检测到黑名单规则配置变更，重新加载...")
                            self.load_rules()
                except Exception as e:
                    print(f"监控黑名单规则配置失败: {e}")
                time.sleep(10)

        threading.Thread(target=watch_file, daemon=True).start()

    def check_rules(self, message):
        """检查消息是否触发黑名单规则"""
        with self.lock:
            rules = self.black_rules.copy()

        for rule in rules:
            if rule in message:
                return True, rule
        return False, None

    def add_rule(self, rule):
        """添加黑名单规则"""
        rule = rule.strip()
        with self.lock:
            if rule not in self.black_rules:
                self.black_rules.append(rule)
                self._save_rules()

    def remove_rule(self, rule):
        """移除黑名单规则"""
        rule = rule.strip()
        with self.lock:
            if rule in self.black_rules:
                self.black_rules.remove(rule)
                self._save_rules()

    def _save_rules(self):
        """保存规则配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write('# 黑名单关键词规则，每行一个\n')
                f.write('# 支持完整匹配\n')
                for rule in self.black_rules:
                    f.write(f'{rule}\n')
            self.file_timestamp = os.path.getmtime(self.config_file)
            print(f"保存黑名单规则配置: {len(self.black_rules)} 条")
        except Exception as e:
            print(f"保存黑名单规则配置失败: {e}")

    def get_rules(self):
        """获取所有黑名单规则"""
        with self.lock:
            return self.black_rules.copy()

    def is_blacklisted(self, content):
        """检查内容是否被黑名单规则拦截"""
        is_blocked, rule = self.check_rules(content)
        return is_blocked