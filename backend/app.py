from flask import Flask
from backend.routes.data_routes import data_bp

app = Flask(__name__)

# Register the dataset API blueprint
app.register_blueprint(data_bp)

@app.route('/')
def home():
    return "Smart Wi-Fi Bandwidth Sharing Backend Running"

if __name__ == '__main__':
    app.run(debug=True, port=5000)