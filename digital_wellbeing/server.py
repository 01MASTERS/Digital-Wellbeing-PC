"""Private dashboard and control API bound only to the local computer."""

import json
import logging
import secrets
import threading
from collections.abc import Callable
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from digital_wellbeing.platform_windows import is_autostart_enabled, set_autostart
from digital_wellbeing.service import WellbeingService
from digital_wellbeing.storage import Store

LOGGER = logging.getLogger(__name__)
WEB_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/logo.svg": ("logo.svg", "image/svg+xml"),
    "/logo.png": ("icon-512.png", "image/png"),
    "/icon-192.png": ("icon-192.png", "image/png"),
    "/icon-512.png": ("icon-512.png", "image/png"),
    "/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json"),
}


class LocalServer:
    def __init__(
        self,
        service: WellbeingService,
        store: Store,
        port: int = 8765,
        on_quit: Callable[[], None] | None = None,
        autostart_get: Callable[[], bool] = is_autostart_enabled,
        autostart_set: Callable[[bool], None] = set_autostart,
    ) -> None:
        self.service = service
        self.store = store
        self.port = port
        self.on_quit = on_quit
        self.autostart_get = autostart_get
        self.autostart_set = autostart_set
        self.token = secrets.token_urlsafe(32)
        self.web_dir = Path(__file__).resolve().parent / "web"
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._httpd is not None:
            return
        controller = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "DigitalWellbeing/1.0"

            def log_message(self, format: str, *args: object) -> None:
                LOGGER.debug("%s - %s", self.address_string(), format % args)

            def _headers(self, content_type: str, length: int, status: int = 200, cache_control: str = "no-store") -> None:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(length))
                self.send_header("Cache-Control", cache_control)
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("X-Frame-Options", "DENY")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header(
                    "Content-Security-Policy",
                    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                    "font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: https:; "
                    "connect-src 'self'; object-src 'none'; frame-ancestors 'none'",
                )
                self.end_headers()

            def _json(self, value: object, status: int = 200) -> None:
                body = json.dumps(value, ensure_ascii=False).encode("utf-8")
                self._headers("application/json; charset=utf-8", len(body), status)
                self.wfile.write(body)

            def _reject(self, status: int, message: str) -> None:
                self._json({"error": message}, status)

            def _host_allowed(self) -> bool:
                return self.headers.get("Host") in {
                    f"127.0.0.1:{controller.port}",
                    f"localhost:{controller.port}",
                }

            def _token_allowed(self) -> bool:
                return secrets.compare_digest(
                    self.headers.get("X-Wellbeing-Token", ""),
                    controller.token,
                )

            def _origin_allowed(self) -> bool:
                origin = self.headers.get("Origin")
                return origin is None or origin in {
                    f"http://127.0.0.1:{controller.port}",
                    f"http://localhost:{controller.port}",
                }

            def _read_json(self) -> dict:
                if not self.headers.get("Content-Type", "").startswith("application/json"):
                    raise ValueError("Send application/json")
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError as error:
                    raise ValueError("Invalid request length") from error
                if not 0 < length <= 65536:
                    raise ValueError("Request body must be between 1 and 65536 bytes")
                try:
                    data = json.loads(self.rfile.read(length))
                except (UnicodeDecodeError, json.JSONDecodeError) as error:
                    raise ValueError("Invalid JSON") from error
                if not isinstance(data, dict):
                    raise TypeError("Request body must be a JSON object")
                return data

            def do_GET(self) -> None:
                if not self._host_allowed():
                    self._reject(HTTPStatus.FORBIDDEN, "Invalid host")
                    return
                parsed = urlsplit(self.path)
                path = parsed.path
                try:
                    if path == "/api/health":
                        self._json({"app": "digital-wellbeing", "version": "1.0"})
                    elif path == "/api/bootstrap":
                        self._json({"token": controller.token})
                    elif path == "/api/snapshot":
                        day = parse_qs(parsed.query).get("day", [None])[0]
                        snapshot = controller.service.snapshot(day)
                        snapshot["autostart"] = controller.autostart_get()
                        self._json(snapshot)
                    elif path == "/api/export.csv":
                        if not self._token_allowed():
                            self._reject(HTTPStatus.FORBIDDEN, "Token required")
                            return
                        body = controller.store.export_csv().encode("utf-8-sig")
                        self._headers("text/csv; charset=utf-8", len(body))
                        self.wfile.write(body)
                    elif path.startswith("/api/icon/site/"):
                        domain = unquote(path[len("/api/icon/site/"):])
                        from digital_wellbeing.icons import get_site_icon
                        icon_bytes, mime = get_site_icon(domain)
                        self._headers(mime, len(icon_bytes), cache_control="public, max-age=3600")
                        self.wfile.write(icon_bytes)
                    elif path.startswith("/api/icon/"):
                        app_id = unquote(path[len("/api/icon/"):])
                        from digital_wellbeing.icons import get_app_icon
                        icon_bytes, mime = get_app_icon(app_id)
                        self._headers(mime, len(icon_bytes), cache_control="public, max-age=3600")
                        self.wfile.write(icon_bytes)
                    elif path in WEB_FILES:
                        filename, content_type = WEB_FILES[path]
                        file_path = controller.web_dir / filename
                        if not file_path.is_file():
                            self._reject(HTTPStatus.NOT_FOUND, "File not found")
                            return
                        body = file_path.read_bytes()
                        self._headers(content_type, len(body))
                        self.wfile.write(body)
                    else:
                        self._reject(HTTPStatus.NOT_FOUND, "Not found")
                except (ValueError, TypeError) as error:
                    self._reject(HTTPStatus.BAD_REQUEST, str(error))
                except (BrokenPipeError, ConnectionResetError):
                    pass
                except Exception:
                    LOGGER.exception("Dashboard GET failed")
                    self._reject(HTTPStatus.INTERNAL_SERVER_ERROR, "Internal error")

            def do_POST(self) -> None:
                if not self._host_allowed() or not self._origin_allowed() or not self._token_allowed():
                    self._reject(HTTPStatus.FORBIDDEN, "Request not authorized")
                    return
                path = urlsplit(self.path).path
                try:
                    data = self._read_json()
                    if path == "/api/settings":
                        controller.service.update_settings(data)
                    elif path == "/api/rule":
                        controller.service.save_rule(data)
                    elif path == "/api/focus/start":
                        controller.service.start_focus(data.get("minutes"))
                    elif path == "/api/focus/stop":
                        controller.service.stop_focus()
                    elif path == "/api/focus/pause":
                        controller.service.pause_focus(data.get("minutes", 5))
                    elif path == "/api/bedtime/start":
                        controller.service.start_bedtime(data.get("minutes", 60))
                    elif path == "/api/bedtime/stop":
                        controller.service.stop_bedtime()
                    elif path == "/api/snooze":
                        app_id = data.get("app_id")
                        if not isinstance(app_id, str):
                            raise TypeError("app_id must be a process name")
                        controller.service.snooze_app(app_id, data.get("minutes", 5))
                    elif path == "/api/autostart":
                        enabled = data.get("enabled")
                        if not isinstance(enabled, bool):
                            raise TypeError("enabled must be true or false")
                        controller.autostart_set(enabled)
                    elif path == "/api/history/delete":
                        if data.get("confirm") != "DELETE":
                            raise ValueError("Type DELETE to confirm")
                        controller.store.clear_history()
                        controller.service.tracker.reset()
                    elif path == "/api/site/rule":
                        controller.service.save_site_rule(data)
                    elif path == "/api/site/tick":
                        domain = data.get("domain", "")
                        seconds = float(data.get("seconds", 5))
                        opened = bool(data.get("opened", False))
                        result = controller.service.record_site_tick(domain, seconds, opened)
                        self._json(result)
                        return
                    elif path == "/api/shortcut":
                        from digital_wellbeing.shortcuts import create_shortcuts
                        created = create_shortcuts()
                        self._json({"ok": True, "created": created})
                        return
                    elif path == "/api/quit":
                        if controller.on_quit is None:
                            raise ValueError("Quit is unavailable")
                    else:
                        self._reject(HTTPStatus.NOT_FOUND, "Not found")
                        return
                    self._json({"ok": True})
                    if path == "/api/quit" and controller.on_quit is not None:
                        threading.Thread(target=controller.on_quit, name="dashboard-quit", daemon=True).start()
                except (ValueError, TypeError) as error:
                    self._reject(HTTPStatus.BAD_REQUEST, str(error))
                except Exception:
                    LOGGER.exception("Dashboard POST failed")
                    self._reject(HTTPStatus.INTERNAL_SERVER_ERROR, "Internal error")

        self._httpd = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        self._httpd.daemon_threads = True
        self.port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, name="wellbeing-http", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._httpd is None:
            return
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread is not None and threading.current_thread() is not self._thread:
            self._thread.join(timeout=3)
        self._thread = None
        self._httpd = None
