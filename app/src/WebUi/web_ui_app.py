import csv
import io
import os
import zipfile
from datetime import datetime
from zoneinfo import ZoneInfo

import yaml
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from src.AiCore.ai_factory import create_ai_client_from_config
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

    def _format_export_timestamp():
        return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d_%H%M%S")

    def _export_rows(messages):
        header = ["id", "group_id", "user_id", "username", "message_id", "message", "raw_message", "created_at"]
        rows = []
        for msg in messages:
            rows.append([
                msg.get("id", ""),
                msg.get("group_id", ""),
                msg.get("user_id", ""),
                msg.get("username", ""),
                msg.get("message_id", ""),
                msg.get("message", ""),
                msg.get("raw_message", ""),
                msg.get("created_at", ""),
            ])
        return header, rows

    def _build_csv_bytes(messages):
        output = io.StringIO()
        writer = csv.writer(output)
        header, rows = _export_rows(messages)
        writer.writerow(header)
        writer.writerows(rows)
        return output.getvalue().encode("utf-8-sig")

    def _build_yaml_bytes(payload):
        text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
        return text.encode("utf-8")

    def _group_payload(group_id, messages):
        return {
            "group_id": str(group_id),
            "exported_at": datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S"),
            "messages": messages,
        }

    def _all_payload(grouped):
        return {
            "exported_at": datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S"),
            "groups": grouped,
        }

    @app.get("/api/chat/export/group/<group_id>")
    def export_group(group_id):
        export_format = request.args.get("format", "csv").lower()
        messages = chat_store.fetch_group_messages_for_export(group_id)
        timestamp = _format_export_timestamp()
        if export_format == "yaml":
            payload = _group_payload(group_id, messages)
            data = _build_yaml_bytes(payload)
            filename = f"chat_{group_id}_{timestamp}.yaml"
            return send_file(io.BytesIO(data), mimetype="text/yaml", as_attachment=True, download_name=filename)
        data = _build_csv_bytes(messages)
        filename = f"chat_{group_id}_{timestamp}.csv"
        return send_file(io.BytesIO(data), mimetype="text/csv", as_attachment=True, download_name=filename)

    @app.get("/api/chat/export/all")
    def export_all_groups():
        export_format = request.args.get("format", "csv").lower()
        grouped = chat_store.fetch_all_messages_grouped()
        timestamp = _format_export_timestamp()
        if export_format == "yaml":
            payload = _all_payload(grouped)
            data = _build_yaml_bytes(payload)
            filename = f"chat_all_{timestamp}.yaml"
            return send_file(io.BytesIO(data), mimetype="text/yaml", as_attachment=True, download_name=filename)
        all_messages = []
        for messages in grouped.values():
            all_messages.extend(messages)
        data = _build_csv_bytes(all_messages)
        filename = f"chat_all_{timestamp}.csv"
        return send_file(io.BytesIO(data), mimetype="text/csv", as_attachment=True, download_name=filename)

    @app.get("/api/chat/export/all-zip")
    def export_all_groups_zip():
        export_format = request.args.get("format", "csv").lower()
        grouped = chat_store.fetch_all_messages_grouped()
        timestamp = _format_export_timestamp()
        extension = "yaml" if export_format == "yaml" else "csv"
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for group_id, messages in grouped.items():
                if extension == "yaml":
                    payload = _group_payload(group_id, messages)
                    data = _build_yaml_bytes(payload)
                else:
                    data = _build_csv_bytes(messages)
                filename = f"group_{group_id}.{extension}"
                zipf.writestr(filename, data)
        buffer.seek(0)
        zip_name = f"chat_all_{timestamp}.zip"
        return send_file(buffer, mimetype="application/zip", as_attachment=True, download_name=zip_name)

    @app.post("/api/ai/test")
    def test_ai():
        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", "Hi"))
        info2ai_config = payload.get("info2ai")
        if not isinstance(info2ai_config, dict):
            config = AppConfigStore.get()
            info2ai_config = config.get("info2ai", {}) or {}
        try:
            client = create_ai_client_from_config(info2ai_config, use_env=False)
            client.load_knowledge_base()
            client.load_history()
            response = client.chat(message)
            if not response:
                return jsonify({"success": False, "error": "未获取到模型回复"}), 500
            return jsonify({"success": True, "response": response})
        except Exception as exc:
            return jsonify({"success": False, "error": str(exc)}), 500

    def read_log_lines(log_path, limit):
        if limit <= 0:
            limit = 200
        if not os.path.exists(log_path):
            return []
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            return [line.rstrip("\n") for line in lines[-limit:]]
        except Exception:
            return []

    @app.get("/api/logs/system")
    def get_system_logs():
        limit = request.args.get("limit", 200)
        try:
            limit = int(limit)
        except ValueError:
            limit = 200
        limit = min(max(limit, 1), 2000)
        log_path = os.path.join(APP_ROOT, "log", "sys.log")
        lines = read_log_lines(log_path, limit)
        updated_at = ""
        if os.path.exists(log_path):
            updated_at = datetime.fromtimestamp(os.path.getmtime(log_path)).strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({"success": True, "lines": lines, "updated_at": updated_at})

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
