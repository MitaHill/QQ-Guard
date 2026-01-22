from src.AppConfig.app_config_store import AppConfigStore


class MonitorGroups:
    def __init__(self):
        self.groups = []
        self._config_version = -1
        self.load_groups()

    def load_groups(self):
        """加载监控群组列表"""
        config = AppConfigStore.get()
        groups = config.get("monitor_groups", [])
        self.groups = [int(group) for group in groups if str(group).isdigit()]
        self._config_version = AppConfigStore.version()
        print(f"加载监控群组: {self.groups}")

    def _ensure_latest(self):
        AppConfigStore.get()
        if AppConfigStore.version() != self._config_version:
            self.load_groups()

    def get_groups(self):
        """获取监控群组列表"""
        self._ensure_latest()
        return self.groups.copy()

    def add_group(self, group_id):
        """添加监控群组"""
        group_id = int(group_id)
        self._ensure_latest()
        if group_id not in self.groups:
            self.groups.append(group_id)
            self._save_groups()

    def remove_group(self, group_id):
        """移除监控群组"""
        group_id = int(group_id)
        self._ensure_latest()
        if group_id in self.groups:
            self.groups.remove(group_id)
            self._save_groups()

    def _save_groups(self):
        """保存群组配置到文件"""
        config = AppConfigStore.get()
        config["monitor_groups"] = self.groups.copy()
        AppConfigStore.save(config)
        self._config_version = AppConfigStore.version()
        print(f"保存监控群组配置: {self.groups}")

    def is_monitored(self, group_id):
        """检查群组是否被监控"""
        self._ensure_latest()
        return int(group_id) in self.groups
