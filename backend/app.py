import os

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from backend.routes.data_routes import data_bp
from backend.routes.bandwidth_routes import bandwidth_bp
from backend.routes.auth_routes import auth_bp
from backend.routes.network_routes import network_bp

# Serve the BUILT React frontend (frontend/dist) from Flask
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend", "dist")

# static_folder=None → we serve the SPA ourselves via one catch-all
# route below (Flask's built-in static rule otherwise shadows it).
app = Flask(__name__, static_folder=None)

# Allow any origin (LAN phones/laptops) to call the API
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register API blueprints
app.register_blueprint(data_bp)
app.register_blueprint(bandwidth_bp, url_prefix="/api")
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(network_bp, url_prefix="/api")


@app.route('/')
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route('/api/health')
def health():
    return jsonify({"ok": True, "service": "smart-wifi-backend"})


# SPA catch-all: serves real files (JS/CSS/images) from dist/,
# and index.html for every client-side route (/dashboard,
# /analytics, ...) so refresh or direct links never 404.
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def spa(path):
    if path.startswith("api/") or path == "api":
        return jsonify({"status": "error", "message": "Not found"}), 404

    if path:
        candidate = os.path.normpath(os.path.join(FRONTEND_DIR, path))
        # Security: never escape the dist folder
        if candidate.startswith(os.path.normpath(FRONTEND_DIR)) and os.path.isfile(candidate):
            return send_from_directory(FRONTEND_DIR, path)

    return send_from_directory(FRONTEND_DIR, "index.html")


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))

    # Production WSGI server: stable, multi-threaded, no debug reloader,
    # survives long sessions (use start_server.bat for auto-restart).
    try:
        from waitress import serve
        print(f"* Smart WiFi app running on http://0.0.0.0:{port}")
        serve(app, host="0.0.0.0", port=port, threads=8)
    except ImportError:
        # Fallback if waitress is not installed yet
        app.run(host="0.0.0.0", port=port, debug=False)
