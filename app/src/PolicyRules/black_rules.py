from src.AppConfig.app_config_store import AppConfigStore


class BlackRulesChecker:
    def __init__(self):
        self.black_rules = []
        self._config_version = -1
        self.load_rules()

    def load_rules(self):
        """加载黑名单规则"""
        config = AppConfigStore.get()
        rules = config.get("black_rules", [])
        self.black_rules = [str(rule) for rule in rules if str(rule)]
        self._config_version = AppConfigStore.version()
        print(f"加载黑名单规则: {len(self.black_rules)} 条")

    def _ensure_latest(self):
        AppConfigStore.get()
        if AppConfigStore.version() != self._config_version:
            self.load_rules()

    def check_rules(self, message):
        """检查消息是否触发黑名单规则"""
        self._ensure_latest()
        rules = self.black_rules.copy()

        for rule in rules:
            if rule in message:
                return True, rule
        return False, None

    def add_rule(self, rule):
        """添加黑名单规则"""
        rule = rule.strip()
        self._ensure_latest()
        if rule not in self.black_rules:
            self.black_rules.append(rule)
            self._save_rules()

    def remove_rule(self, rule):
        """移除黑名单规则"""
        rule = rule.strip()
        self._ensure_latest()
        if rule in self.black_rules:
            self.black_rules.remove(rule)
            self._save_rules()

    def _save_rules(self):
        """保存规则配置到文件"""
        config = AppConfigStore.get()
        config["black_rules"] = self.black_rules.copy()
        AppConfigStore.save(config)
        self._config_version = AppConfigStore.version()
        print(f"保存黑名单规则配置: {len(self.black_rules)} 条")

    def get_rules(self):
        """获取所有黑名单规则"""
        self._ensure_latest()
        return self.black_rules.copy()

    def is_blacklisted(self, content):
        """检查内容是否被黑名单规则拦截"""
        is_blocked, rule = self.check_rules(content)
        return is_blocked
