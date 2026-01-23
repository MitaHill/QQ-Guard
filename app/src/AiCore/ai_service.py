from src.AiCore.ai_factory import create_ai_client


class AiService:
    def __init__(self, sys_logger=None):
        self.is_ready = False
        self.client = None
        self.sys_logger = sys_logger

    def start_service(self):
        """初始化AI服务"""
        self._log_info("ai_service", "init_start", {})
        try:
            self.client = create_ai_client()
            self._log_info("ai_service", "load_knowledge", {})
            self.client.load_knowledge_base()
            self.client.load_history()

            self._log_info("ai_service", "warmup", {})
            response = self.client.chat("ready")
            if response:
                self.is_ready = True
                self._log_info("ai_service", "init_success", {})
            else:
                self._log_error("ai_service", "init_failed", {"reason": "empty_response"})
        except Exception as e:
            self._log_error("ai_service", "init_failed", {"error": str(e)})
            import traceback
            self._log_error("ai_service", "init_failed_trace", {"trace": traceback.format_exc()})

    def judge_message(self, user_id, message):
        """使用AI判断消息是否违规"""
        if not self.is_ready:
            self._log_warning("ai_service", "skip_not_ready", {"user_id": str(user_id)})
            return False

        self._log_info("ai_service", "judge_start", {"user_id": str(user_id), "message": message})

        try:
            formatted_message = f"QQ号{user_id}发送了：{message}"
            self._log_info("ai_service", "judge_formatted", {"user_id": str(user_id), "formatted_message": formatted_message})

            import time
            start_time = time.time()
            result = self.client.judge(formatted_message) if self.client else False
            response_time = time.time() - start_time

            is_violation = result is True
            self._log_info("ai_service", "judge_result", {
                "user_id": str(user_id),
                "raw_result": result,
                "is_violation": is_violation,
                "response_time_seconds": round(response_time, 3),
            })
            return is_violation

        except Exception as e:
            self._log_error("ai_service", "judge_error", {"user_id": str(user_id), "error": str(e)})
            import traceback
            self._log_error("ai_service", "judge_error_trace", {"trace": traceback.format_exc()})
            return False

    def stop_service(self):
        """停止AI服务"""
        if self.is_ready:
            self._log_info("ai_service", "stop", {})
            self.is_ready = False
            self.client = None
            self._log_info("ai_service", "stopped", {})
        else:
            self._log_info("ai_service", "stop_skip_not_running", {})

    def _log_info(self, module, action, data):
        if self.sys_logger:
            self.sys_logger.info_event(module, action, data)
        else:
            print(f"[{module}] {action} {data}")

    def _log_warning(self, module, action, data):
        if self.sys_logger:
            self.sys_logger.warning_event(module, action, data)
        else:
            print(f"[{module}] {action} {data}")

    def _log_error(self, module, action, data):
        if self.sys_logger:
            self.sys_logger.error_event(module, action, data)
        else:
            print(f"[{module}] {action} {data}")


if __name__ == "__main__":
    print("初始化AI系统...")
    service = AiService()
    service.start_service()
