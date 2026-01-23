import queue
import threading


class AIQueue:
    def __init__(self, ai_api, csv_logger, sys_logger):
        self.ai_queue = queue.Queue()
        self.ai_worker_running = True
        self.ai_api = ai_api
        self.csv_logger = csv_logger
        self.sys_logger = sys_logger
        self.recaller = None
        self.admin_notifier = None
        self.violation_stats = None
        self.stats_lock = None

    def set_dependencies(self, recaller, admin_notifier, violation_stats, stats_lock):
        """设置依赖项"""
        self.recaller = recaller
        self.admin_notifier = admin_notifier
        self.violation_stats = violation_stats
        self.stats_lock = stats_lock

    def start_worker(self):
        """启动AI工作队列"""

        def ai_worker():
            while self.ai_worker_running:
                try:
                    task = self.ai_queue.get(timeout=30)
                    if task is None:
                        break
                    user_id, username, group_id, message_id, parsed_message = task
                    self._process_ai_message(user_id, username, group_id, message_id, parsed_message)
                    self.ai_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    self.sys_logger.error_event("ai_queue", "worker_error", {"error": str(e)})

        threading.Thread(target=ai_worker, daemon=True).start()
        self.sys_logger.info("AI队列工作线程已启动")

    def add_message(self, user_id, username, group_id, message_id, parsed_message):
        """添加消息到队列"""
        self.ai_queue.put((user_id, username, group_id, message_id, parsed_message))

    def _process_ai_message(self, user_id, username, group_id, message_id, parsed_message):
        """AI检测消息"""
        import time
        start_time = time.time()

        try:
            self.sys_logger.info_event("ai_queue", "judge_start", {
                "group_id": str(group_id),
                "user_id": str(user_id),
                "username": username,
                "message_id": str(message_id),
                "message": parsed_message,
            })
            is_violation = self.ai_api.judge_message(user_id, parsed_message)
            response_time = time.time() - start_time

            self.sys_logger.info_event("ai_queue", "judge_result", {
                "group_id": str(group_id),
                "user_id": str(user_id),
                "username": username,
                "message_id": str(message_id),
                "message": parsed_message,
                "is_violation": is_violation,
                "response_time_seconds": round(response_time, 3),
            })
            if is_violation:
                success = self.recaller.delete_message(message_id)
                self.csv_logger.log_message(user_id, username, group_id, parsed_message,
                                            success, False, "AI违规", "AI判定违规内容", response_time)
                self._handle_violation_stats(user_id, group_id, "AI判定违规" + ("" if success else " 但撤回失败"))
            else:
                self.csv_logger.log_message(user_id, username, group_id, parsed_message,
                                            False, False, "", "", response_time)

        except Exception as e:
            self.sys_logger.error_event("ai_queue", "judge_error", {
                "group_id": str(group_id),
                "user_id": str(user_id),
                "username": username,
                "message_id": str(message_id),
                "message": parsed_message,
                "error": str(e),
            })
            self.csv_logger.log_message(user_id, username, group_id, parsed_message,
                                        False, False, "异常", str(e), time.time() - start_time)

    def _handle_violation_stats(self, user_id, group_id, action):
        """处理违规统计"""
        with self.stats_lock:
            self.violation_stats[user_id] += 1
        self.admin_notifier.notify_violation(user_id, group_id, action)

    def stop(self):
        """停止队列"""
        self.ai_worker_running = False
        self.ai_queue.put(None)
