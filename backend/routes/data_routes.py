from flask import Blueprint, jsonify
from services.dataset_service import get_dataset_records

data_bp = Blueprint('data_bp', __name__)

@data_bp.route('/api/dataset', methods=['GET'])
def fetch_dataset():
    try:
        data = get_dataset_records(limit=50)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500