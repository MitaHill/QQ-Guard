import time
import threading
from collections import defaultdict
from datetime import datetime

from src.use_qq_bot_api import QQBotAPI
from src.monitor.app import MonitorGroups
from src.white_member import WhiteMemberChecker
from src.white_group import WhiteGroupChecker
from src.white_list_website import WebsiteWhitelistChecker
from src.black_rules import BlackRulesChecker
from src.use_info2ai_api import AI_API
from src.back import MessageRecaller
from src.send_message import MessageSender
from src.log.csv import CSVLogger
from src.log.sys import SystemLogger
from src.draw_top import RankingDrawer
from src.send2 import AdminNotifier
from src.queue import AIQueue


class OneBotTest:
    def __init__(self):
        self.violation_stats = defaultdict(int)
        self.stats_lock = threading.Lock()

        # 初始化模块
        self.qq_api = QQBotAPI()
        self.monitor = MonitorGroups()
        self.white_member = WhiteMemberChecker()
        self.white_group = WhiteGroupChecker()
        self.website_checker = WebsiteWhitelistChecker()
        self.black_rules = BlackRulesChecker()
        self.ai_api = AI_API()
        self.recaller = MessageRecaller(self.qq_api)
        self.sender = MessageSender(self.qq_api)
        self.csv_logger = CSVLogger()
        self.sys_logger = SystemLogger()
        self.ranking_drawer = RankingDrawer()
        self.admin_notifier = AdminNotifier(self.sender)

        self.ai_queue = AIQueue(self.ai_api, self.csv_logger, self.sys_logger)
        self.ai_queue.set_dependencies(self.recaller, self.admin_notifier, self.violation_stats, self.stats_lock)

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

        if self.white_member.is_whitelisted(user_id):
            self.csv_logger.log_message(user_id, username, group_id, parsed_message, is_whitelist=True)
            return

        threading.Thread(target=self.check_message_rules,
                         args=(user_id, username, group_id, message_id, parsed_message, raw_message),
                         daemon=True).start()

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

                time.sleep(1)
            except Exception as e:
                self.sys_logger.error(f"轮询错误: {e}")
                time.sleep(5)

    def start(self):
        self.sys_logger.info(f"监控群组: {self.monitor.get_groups()}")
        self.sys_logger.info("启动消息监控...")

        try:
            self.poll_messages()
        except KeyboardInterrupt:
            self.sys_logger.info("正在退出...")


if __name__ == "__main__":
    OneBotTest().start()