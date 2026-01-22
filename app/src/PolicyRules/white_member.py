from src.AppConfig.app_config_store import AppConfigStore


class WhiteMemberChecker:
    def __init__(self):
        self.white_members = set()
        self._config_version = -1
        self.load_members()

    def load_members(self):
        """加载白名单成员"""
        config = AppConfigStore.get()
        members = config.get("white_members", [])
        self.white_members = set(int(member) for member in members if str(member).isdigit())
        self._config_version = AppConfigStore.version()
        print(f"加载白名单成员: {len(self.white_members)} 个")

    def _ensure_latest(self):
        AppConfigStore.get()
        if AppConfigStore.version() != self._config_version:
            self.load_members()

    def is_whitelisted(self, user_id):
        """检查用户是否在白名单"""
        self._ensure_latest()
        return int(user_id) in self.white_members

    def add_member(self, user_id):
        """添加白名单成员"""
        user_id = int(user_id)
        self._ensure_latest()
        self.white_members.add(user_id)
        self._save_members()

    def remove_member(self, user_id):
        """移除白名单成员"""
        user_id = int(user_id)
        self._ensure_latest()
        self.white_members.discard(user_id)
        self._save_members()

    def _save_members(self):
        """保存成员配置到文件"""
        config = AppConfigStore.get()
        config["white_members"] = sorted(self.white_members)
        AppConfigStore.save(config)
        self._config_version = AppConfigStore.version()
        print(f"保存白名单成员配置: {len(self.white_members)} 个")

    def get_members(self):
        """获取所有白名单成员"""
        self._ensure_latest()
        return list(self.white_members)
