from flask import Flask, send_from_directory
from backend.routes.bandwidth_routes import bandwidth_bp
import os


# Path to frontend folder
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)


app = Flask(
    __name__,
    static_folder=FRONTEND_DIR
)


# Register API routes
app.register_blueprint(
    bandwidth_bp,
    url_prefix="/api"
)


# Home page
@app.route("/")
def home():

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# Frontend CSS / JS / files
@app.route("/<path:filename>")
def frontend_files(filename):

    return send_from_directory(
        FRONTEND_DIR,
        filename
    )


if __name__ == "__main__":

    print(
        "======================================"
    )

    print(
        " SMART WI-FI BANDWIDTH SHARING"
    )

    print(
        "======================================"
    )

    print(
        "Server running at:"
    )

    print(
        "http://127.0.0.1:5000"
    )

    app.run(
        debug=True
    )