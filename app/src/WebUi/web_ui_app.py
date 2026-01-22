import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from src.AppConfig.app_config_store import APP_ROOT, AppConfigStore
from src.DataStore.chat_history_store import ChatHistoryStore


def create_app():
    web_root = os.path.abspath(os.path.join(APP_ROOT, "WebUI"))
    dist_dir = os.path.join(web_root, "dist")
    static_dir = dist_dir if os.path.exists(os.path.join(dist_dir, "index.html")) else None

    app = Flask(__name__, static_folder=static_dir)
    cors_origins = os.getenv(
        "QQ_GUARD_WEB_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    CORS(app, origins=[o.strip() for o in cors_origins if o.strip()])

    chat_store = ChatHistoryStore()

    @app.get("/api/health")
    def health():
        return jsonify({"success": True})

    @app.get("/api/config")
    def get_config():
        config = AppConfigStore.get()
        return jsonify({"success": True, "version": AppConfigStore.version(), "config": config})

    @app.get("/api/config/version")
    def get_config_version():
        AppConfigStore.get()
        return jsonify({"success": True, "version": AppConfigStore.version()})

    @app.put("/api/config")
    def update_config():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"success": False, "error": "配置必须是 JSON 对象"}), 400
        AppConfigStore.save(payload)
        return jsonify({"success": True, "version": AppConfigStore.version()})

    @app.patch("/api/config/section/<key>")
    def update_config_section(key):
        payload = request.get_json(silent=True)
        if payload is None:
            return jsonify({"success": False, "error": "配置内容不能为空"}), 400
        config = AppConfigStore.get()
        config[key] = payload
        AppConfigStore.save(config)
        return jsonify({"success": True, "version": AppConfigStore.version()})

    @app.get("/api/chat/groups")
    def list_groups():
        groups = chat_store.list_groups()
        return jsonify({"success": True, "groups": groups})

    @app.get("/api/chat/groups/<group_id>/messages")
    def get_group_messages(group_id):
        limit = request.args.get("limit", 100)
        offset = request.args.get("offset", 0)
        messages = chat_store.fetch_group_messages(group_id, limit=limit, offset=offset)
        return jsonify({"success": True, "messages": messages})

    if static_dir:
        @app.get("/")
        def serve_index():
            return send_from_directory(static_dir, "index.html")

        @app.get("/<path:path>")
        def serve_static(path):
            full_path = os.path.join(static_dir, path)
            if os.path.exists(full_path):
                return send_from_directory(static_dir, path)
            return send_from_directory(static_dir, "index.html")
    else:
        @app.get("/")
        def root_hint():
            return jsonify({
                "success": True,
                "message": "前端尚未构建，请运行 web-ui 开发服务器或构建 dist。"
            })

    return app


def main():
    host = os.getenv("QQ_GUARD_WEB_HOST", "0.0.0.0")
    port = int(os.getenv("QQ_GUARD_WEB_PORT", "5000"))
    app = create_app()
    app.run(host=host, port=port)


if __name__ == "__main__":
    main()
