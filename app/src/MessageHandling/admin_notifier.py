from src.AppConfig.app_config_store import AppConfigStore


class AdminNotifier:
    def __init__(self, message_sender):
        self.sender = message_sender
        self.admins = []
        self._config_version = -1
        self.load_admins()

    def load_admins(self):
        """加载管理员列表"""
        config = AppConfigStore.get()
        admins = config.get("admins", [])
        self.admins = [int(admin) for admin in admins if str(admin).isdigit()]
        self._config_version = AppConfigStore.version()
        print(f"加载管理员列表: {len(self.admins)} 个")

    def _ensure_latest(self):
        AppConfigStore.get()
        if AppConfigStore.version() != self._config_version:
            self.load_admins()

    def notify_violation(self, user_id, group_id, action):
        """通知管理员违规消息"""
        message = f"{user_id} 已被{action}消息在群号 {group_id} 中"
        self._ensure_latest()
        admin_list = self.admins.copy()

        for admin_id in admin_list:
            try:
                self.sender.send_private_message(admin_id, message)
            except Exception as e:
                print(f"发送通知给管理员 {admin_id} 失败: {e}")

    def send_ranking(self, ranking_text):
        """发送排行榜给管理员"""
        print(f"[AdminNotifier] 开始发送文字排行榜...")

        self._ensure_latest()
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
        self._ensure_latest()
        return self.admins.copy()

    def add_admin(self, admin_id):
        """添加管理员"""
        admin_id = int(admin_id)
        self._ensure_latest()
        if admin_id not in self.admins:
            self.admins.append(admin_id)
            self._save_admins()

    def remove_admin(self, admin_id):
        """移除管理员"""
        admin_id = int(admin_id)
        self._ensure_latest()
        if admin_id in self.admins:
            self.admins.remove(admin_id)
            self._save_admins()

    def _save_admins(self):
        """保存管理员配置"""
        config = AppConfigStore.get()
        config["admins"] = self.admins.copy()
        AppConfigStore.save(config)
        self._config_version = AppConfigStore.version()
        print(f"保存管理员配置: {len(self.admins)} 个")
