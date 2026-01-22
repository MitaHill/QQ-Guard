import json
import time
import threading
from collections import defaultdict

from src.BotApi.onebot_http_client import OneBotHttpClient
from src.BotApi.onebot_ws_client import OneBotWebSocketClient
from src.BotApi.onebot_http_post_server import OneBotHttpPostServer
from src.Monitoring.monitor_groups import MonitorGroups
from src.PolicyRules.white_member import WhiteMemberChecker
from src.PolicyRules.white_group import WhiteGroupChecker
from src.PolicyRules.white_list_website import WebsiteWhitelistChecker
from src.PolicyRules.black_rules import BlackRulesChecker
from src.AiCore.ai_service import AiService
from src.MessageHandling.message_recaller import MessageRecaller
from src.MessageHandling.message_sender import MessageSender
from src.Logging.csv_logger import CSVLogger
from src.Logging.system_logger import SystemLogger
from src.Reporting.ranking_drawer import RankingDrawer
from src.MessageHandling.admin_notifier import AdminNotifier
from src.TaskQueue.ai_queue import AIQueue
from src.AppConfig.app_config_store import AppConfigStore
from src.DataStore.chat_history_store import ChatHistoryStore


class OneBotTest:
    def __init__(self):
        self.violation_stats = defaultdict(int)
        self.stats_lock = threading.Lock()

        # 初始化模块
        self.qq_api = OneBotHttpClient()
        self.monitor = MonitorGroups()
        self.white_member = WhiteMemberChecker()
        self.white_group = WhiteGroupChecker()
        self.website_checker = WebsiteWhitelistChecker()
        self.black_rules = BlackRulesChecker()
        self.ai_api = AiService()
        self.recaller = MessageRecaller(self.qq_api)
        self.sender = MessageSender(self.qq_api)
        self.csv_logger = CSVLogger()
        self.sys_logger = SystemLogger()
        self.ranking_drawer = RankingDrawer()
        self.admin_notifier = AdminNotifier(self.sender)

        self.ai_queue = AIQueue(self.ai_api, self.csv_logger, self.sys_logger)
        self.ai_queue.set_dependencies(self.recaller, self.admin_notifier, self.violation_stats, self.stats_lock)
        self.ws_client = None
        self.http_post_server = None
        self.chat_history = ChatHistoryStore()

        self.init_system()

    def init_system(self):
        self.ai_api.start_service()
        self.start_timers()
        self.ai_queue.start_worker()
        self.sys_logger.info("系统初始化完成")

    def start_timers(self):
        def flush_logs():
            self.csv_logger.flush()
            threading.Timer(20.0, flush_logs).start()

        def send_ranking():
            ranking_text = self.ranking_drawer.create_ranking_text(self.violation_stats)
            self.admin_notifier.send_ranking(ranking_text)
            threading.Timer(3600.0, send_ranking).start()

        flush_logs()
        send_ranking()

    def process_message(self, msg):
        user_id = msg.get("user_id")
        group_id = msg.get("group_id")
        message_id = msg.get("message_id")
        raw_message = msg.get("message", "")

        if not all([user_id, group_id, message_id, raw_message]):
            return

        username = self.qq_api.get_user_info(user_id, group_id)
        parsed_message = self.qq_api.parse_message(raw_message).strip()
        self.store_chat_message(group_id, user_id, username, message_id, parsed_message, raw_message)

        if self.white_member.is_whitelisted(user_id):
            self.csv_logger.log_message(user_id, username, group_id, parsed_message, is_whitelist=True)
            return

        threading.Thread(target=self.check_message_rules,
                         args=(user_id, username, group_id, message_id, parsed_message, raw_message),
                         daemon=True).start()

    def store_chat_message(self, group_id, user_id, username, message_id, parsed_message, raw_message):
        normalized_raw = raw_message
        if not isinstance(raw_message, str):
            try:
                normalized_raw = json.dumps(raw_message, ensure_ascii=False)
            except Exception:
                normalized_raw = str(raw_message)
        try:
            self.chat_history.add_message(
                group_id=group_id,
                user_id=user_id,
                username=username,
                message_id=message_id,
                message=parsed_message,
                raw_message=normalized_raw,
            )
        except Exception as exc:
            self.sys_logger.error(f"写入聊天记录失败: {exc}")

    def handle_event(self, event):
        if not isinstance(event, dict):
            return
        if event.get("post_type") != "message":
            return
        if event.get("message_type") != "group":
            return
        group_id = event.get("group_id")
        if not group_id or not self.monitor.is_monitored(group_id):
            return
        self.process_message(event)

    def check_message_rules(self, user_id, username, group_id, message_id, parsed_message, raw_message):
        if not parsed_message:
            return

        # 群聊分享检查
        is_group_share, is_share_whitelisted, shared_group_id = self.white_group.check_group_share(raw_message)
        if is_group_share and not is_share_whitelisted:
            self.handle_violation(user_id, username, group_id, message_id, parsed_message,
                                  "群聊分享违规", f"非白名单群聊: {shared_group_id}")
            return

        # 网站检查
        is_website_ok, domains = self.website_checker.check_whitelist(parsed_message)
        if not is_website_ok:
            self.handle_violation(user_id, username, group_id, message_id, parsed_message,
                                  "网站违规", f"非白名单网站: {domains}")
            return

        # 黑名单检查
        is_blacklisted, rule = self.black_rules.check_rules(parsed_message)
        if is_blacklisted:
            self.handle_violation(user_id, username, group_id, message_id, parsed_message,
                                  "黑名单违规", f"触发规则: {rule}")
            return

        # AI检测
        self.ai_queue.add_message(user_id, username, group_id, message_id, parsed_message)

    def handle_violation(self, user_id, username, group_id, message_id, parsed_message, violation_type, reason):
        success = self.recaller.delete_message(message_id)
        self.csv_logger.log_message(user_id, username, group_id, parsed_message, success, False, violation_type, reason)

        with self.stats_lock:
            self.violation_stats[user_id] += 1

        action_text = violation_type + ("" if success else " 但撤回失败")
        self.admin_notifier.notify_violation(user_id, group_id, action_text)

    def poll_messages(self):
        last_message_ids = set()

        while True:
            try:
                config = AppConfigStore.get()
                poll_interval = config.get("app", {}).get("polling_interval", 1)
                for group_id in self.monitor.get_groups():
                    messages = self.qq_api.get_group_messages(group_id)

                    for msg in reversed(messages):
                        message_id = msg.get("message_id")
                        if message_id and message_id not in last_message_ids:
                            last_message_ids.add(message_id)

                            if time.time() - msg.get("time", 0) > 300:
                                continue

                            msg["group_id"] = group_id
                            self.process_message(msg)

                    if len(last_message_ids) > 1000:
                        last_message_ids = set(list(last_message_ids)[-500:])

                time.sleep(poll_interval)
            except Exception as e:
                self.sys_logger.error(f"轮询错误: {e}")
                time.sleep(5)

    def start_websocket(self):
        ws_url = self.qq_api.ws_url
        if not ws_url:
            self.sys_logger.error("WebSocket 模式缺少 qq_bot_api.ws_url 配置")
            return
        self.sys_logger.info(f"WebSocket 模式启动: {ws_url}")
        self.ws_client = OneBotWebSocketClient(
            ws_url=ws_url,
            token=self.qq_api.token,
            on_event=self.handle_event,
            logger=self.sys_logger,
            reconnect_seconds=self.qq_api.ws_reconnect_seconds,
            ping_interval_seconds=self.qq_api.ws_ping_interval_seconds,
        )
        self.ws_client.start()

    def start_http_post(self):
        self.http_post_server = OneBotHttpPostServer(
            host=self.qq_api.http_post_host,
            port=self.qq_api.http_post_port,
            path=self.qq_api.http_post_path,
            token=self.qq_api.token,
            secret=self.qq_api.http_post_secret,
            on_event=self.handle_event,
            logger=self.sys_logger,
        )
        self.http_post_server.start()

    def start(self):
        self.sys_logger.info(f"监控群组: {self.monitor.get_groups()}")
        self.sys_logger.info("启动消息监控...")

        try:
            mode = str(self.qq_api.mode or "http_post").lower()
            if mode in {"websocket", "ws"}:
                self.start_websocket()
            elif mode in {"http_post", "http"}:
                self.start_http_post()
            else:
                self.poll_messages()
        except KeyboardInterrupt:
            self.sys_logger.info("正在退出...")
            if self.ws_client:
                self.ws_client.stop()
            if self.http_post_server:
                self.http_post_server.stop()


if __name__ == "__main__":
    OneBotTest().start()
