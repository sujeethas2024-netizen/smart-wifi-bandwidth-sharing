<<<<<<< HEAD
from flask import Flask, send_from_directory
from backend.routes.bandwidth_routes import bandwidth_bp
import os
=======
from flask import Flask
from routes.data_routes import data_bp
>>>>>>> 619d6ac5eb60381adee12dc026bac9aa261adeb5

app = Flask(__name__)

# Register the dataset API blueprint
app.register_blueprint(data_bp)

@app.route('/')
def home():
    return "Smart Wi-Fi Bandwidth Sharing Backend Running!"

if __name__ == '__main__':
    app.run(debug=True, port=5000)