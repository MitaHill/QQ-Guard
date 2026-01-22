import json
import threading
import time

import websocket


class OneBotWebSocketClient:
    def __init__(self, ws_url, token, on_event, logger, reconnect_seconds=5, ping_interval_seconds=30):
        self.ws_url = ws_url
        self.token = token
        self.on_event = on_event
        self.logger = logger
        self.reconnect_seconds = reconnect_seconds
        self.ping_interval_seconds = ping_interval_seconds
        self._stop_event = threading.Event()
        self._ws_app = None

    def _build_headers(self):
        if not self.token:
            return []
        return [f"Authorization: Bearer {self.token}"]

    def _on_open(self, ws):
        self.logger.info(f"WebSocket 已连接: {self.ws_url}")

    def _on_message(self, ws, message):
        try:
            payload = json.loads(message)
        except Exception as exc:
            self.logger.error(f"WebSocket 消息解析失败: {exc}")
            return

        try:
            if isinstance(payload, list):
                for item in payload:
                    if isinstance(item, dict):
                        self.on_event(item)
                return
            if isinstance(payload, dict):
                self.on_event(payload)
                return
            self.logger.warning("WebSocket 收到非 JSON 对象消息")
        except Exception as exc:
            self.logger.error(f"处理 WebSocket 事件失败: {exc}")

    def _on_error(self, ws, error):
        self.logger.error(f"WebSocket 错误: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        self.logger.warning(f"WebSocket 已断开: {close_status_code} {close_msg}")

    def start(self):
        if not self.ws_url:
            raise ValueError("WebSocket URL 为空")
        while not self._stop_event.is_set():
            self._ws_app = websocket.WebSocketApp(
                self.ws_url,
                header=self._build_headers(),
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )
            self._ws_app.run_forever(
                ping_interval=self.ping_interval_seconds,
                ping_timeout=max(5, self.ping_interval_seconds + 5),
            )
            if self._stop_event.is_set():
                break
            time.sleep(self.reconnect_seconds)

    def stop(self):
        self._stop_event.set()
        if self._ws_app:
            self._ws_app.close()
