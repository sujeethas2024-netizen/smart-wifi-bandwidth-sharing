from flask import Blueprint, request, jsonify

from services.allocation_service import (
    allocate_bandwidth
)


bandwidth_bp = Blueprint(
    "bandwidth",
    __name__
)


@bandwidth_bp.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({
        "status": "success",
        "message": "Smart Wi-Fi backend is running"
    })


@bandwidth_bp.route(
    "/allocate",
    methods=["POST"]
)
def allocate():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "status": "error",
                "message": "Request body is empty"
            }), 400


        total_bandwidth = float(
            data.get(
                "total_bandwidth",
                40
            )
        )


        users = data.get(
            "users",
            []
        )


        if not users:

            return jsonify({
                "status": "error",
                "message": "No users provided"
            }), 400


        result = allocate_bandwidth(
            total_bandwidth,
            users
        )


        return jsonify({

            "status": "success",

            "data": result

        })


    except Exception as error:

        return jsonify({

            "status": "error",

            "message": str(error)

        }), 500