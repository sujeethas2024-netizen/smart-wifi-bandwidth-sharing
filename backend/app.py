"""
Smart WiFi Bandwidth Sharing — Flask application entry point.

Serves:
  * the REST API under /api/*  (auth, bandwidth allocation, network stats)
  * the built React frontend from frontend/dist (SPA mode)

Start it with START_APP.bat (recommended) or:  python -m backend.app
"""

import os
import socket

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from backend.routes.data_routes import data_bp
from backend.routes.bandwidth_routes import bandwidth_bp
from backend.routes.auth_routes import auth_bp
from backend.routes.network_routes import network_bp

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend", "dist")
PORT = int(os.environ.get("PORT", 5000))


def lan_ip() -> str:
    """Best-effort detection of this PC's WiFi/LAN IPv4 address.

    Uses a UDP 'connect' trick — no packet is actually sent, it just
    asks the OS which local interface would be used to reach the
    internet, giving us the real WiFi adapter IP (e.g. 192.168.1.5).
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"
    finally:
        sock.close()


def print_banner() -> None:
    """Print the permanent links — same every time, never changes.

    Also renders a scannable QR code of the network URL, both as
    ASCII art in this terminal and saved to qr_code.png — point a
    phone camera at it and the site opens instantly.
    """
    ip = lan_ip()
    url = f"http://{ip}:{PORT}"
    line = "=" * 64

    try:
        import qrcode

        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        # ASCII version for the terminal. Some consoles/redirects can't
        # print the block characters — never let that break the banner.
        try:
            qr.print_ascii(invert=True)
        except Exception:
            pass
        # PNG version for sharing / slides
        img = qr.make_image(fill_color="#1a1a2e", back_color="white")
        img.save(os.path.join(BASE_DIR, "qr_code.png"))
        qr_saved = True
    except Exception:
        qr_saved = False

    print()
    print(line)
    print("    SMART WIFI BANDWIDTH SHARING  —  SERVER RUNNING")
    print(line)
    print(f"    On this PC ........  http://localhost:{PORT}")
    print(f"    On WiFi devices ...  {url}")
    print("                         (open on any phone/laptop")
    print("                          connected to the SAME WiFi)")
    if qr_saved:
        print(f"    Scan the QR above with a phone camera - opens {url}")
        print(f"    A shareable copy was saved to qr_code.png")
    print(line)
    print("    These links are permanent — bookmark them!")
    print("    Keep this window open. Press Ctrl+C to stop.")
    print(line)
    print()


# static_folder=None → we serve the SPA ourselves via one catch-all
# route below (Flask's built-in static rule would otherwise shadow it).
app = Flask(__name__, static_folder=None)

# Allow any origin (LAN phones/laptops + public hosting)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register API blueprints
app.register_blueprint(data_bp)
app.register_blueprint(bandwidth_bp, url_prefix="/api")
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(network_bp, url_prefix="/api")


# NOTE: /api/health is provided by backend/routes/bandwidth_routes.py

# SPA catch-all: serves real files (JS/CSS/images) from dist/,
# and index.html for every client-side route (/dashboard,
# /analytics, ...) so refresh or direct links never 404.
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def spa(path):
    if path.startswith("api/") or path == "api":
        return jsonify({"status": "error", "message": "Not found"}), 404

    if path:
        candidate = os.path.normpath(os.path.join(FRONTEND_DIR, path))
        # Security: never escape the dist folder
        if candidate.startswith(os.path.normpath(FRONTEND_DIR)) and os.path.isfile(candidate):
            return send_from_directory(FRONTEND_DIR, path)

    html_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(html_path):
        content = open(html_path, "r", encoding="utf-8").read()
        api_base = os.environ.get("PUBLIC_API_BASE", "")
        if api_base:
            inject = f"<script>window.__API_BASE__={repr(api_base)}</script>"
            content = content.replace("</head>", f"{inject}</head>")
        return content

    return jsonify({"status": "error", "message": "Frontend not built"}), 500


if __name__ == "__main__":
    print_banner()

    try:
        # Production WSGI server: stable, multi-threaded, no debug
        # reloader — survives long demo sessions.
        from waitress import serve

        serve(app, host="0.0.0.0", port=PORT, threads=8)
    except ImportError:
        # Fallback if waitress is not installed yet
        app.run(host="0.0.0.0", port=PORT, debug=False)
    except OSError:
        print(f"[!] Port {PORT} is already in use.")
        print(f"    The app is probably ALREADY running — just open:")
        print(f"    http://localhost:{PORT}")