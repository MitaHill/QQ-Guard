import hashlib
import hmac
import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class OneBotHttpPostServer:
    def __init__(self, host, port, path, token, secret, on_event, logger):
        self.host = host
        self.port = port
        self.path = path or "/"
        self.token = token
        self.secret = secret
        self.on_event = on_event
        self.logger = logger
        self._server = None
        self._thread = None

    def _make_handler(self):
        server_ref = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                if server_ref.path and self.path.split("?")[0] != server_ref.path:
                    self.send_response(404)
                    self.end_headers()
                    return

                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length) if length > 0 else b""

                if server_ref.token:
                    if not _check_token(self, server_ref.token):
                        server_ref.logger.warning("HTTP POST 鉴权失败: token 不匹配")
                        self.send_response(401)
                        self.end_headers()
                        return

                if server_ref.secret:
                    if not _check_signature(self, server_ref.secret, body):
                        server_ref.logger.warning("HTTP POST 鉴权失败: 签名无效")
                        self.send_response(403)
                        self.end_headers()
                        return

                try:
                    payload = json.loads(body.decode("utf-8"))
                except Exception as exc:
                    server_ref.logger.error(f"HTTP POST 解析 JSON 失败: {exc}")
                    self.send_response(400)
                    self.end_headers()
                    return

                try:
                    server_ref.on_event(payload)
                except Exception as exc:
                    server_ref.logger.error(f"HTTP POST 处理事件失败: {exc}")

                self.send_response(204)
                self.end_headers()

            def log_message(self, format, *args):
                return

        return Handler

    def start(self):
        self._server = ThreadingHTTPServer((self.host, self.port), self._make_handler())
        self.logger.info(f"HTTP POST 服务器启动: http://{self.host}:{self.port}{self.path}")
        self._server.serve_forever()

    def start_in_thread(self):
        self._thread = threading.Thread(target=self.start, daemon=True)
        self._thread.start()

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()


def _check_token(handler, expected_token):
    auth = handler.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[len("Bearer "):] == expected_token

    query = urllib.parse.urlparse(handler.path).query
    params = urllib.parse.parse_qs(query)
    token = params.get("access_token", [""])[0]
    return token == expected_token


def _check_signature(handler, secret, body):
    signature = handler.headers.get("X-Signature", "")
    if not signature.startswith("sha1="):
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha1).hexdigest()
    return signature == f"sha1={expected}"
