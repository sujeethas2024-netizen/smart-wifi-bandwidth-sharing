import os

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from backend.routes.data_routes import data_bp
from backend.routes.bandwidth_routes import bandwidth_bp
from backend.routes.auth_routes import auth_bp
from backend.routes.network_routes import network_bp

# Serve the legacy frontend (frontend/index.html) from Flask
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

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


if __name__ == '__main__':
    # host=0.0.0.0 → reachable from other devices on the same WiFi/LAN
    app.run(debug=True, port=5000, host="0.0.0.0")