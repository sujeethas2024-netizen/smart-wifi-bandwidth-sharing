from flask import Blueprint, request, jsonify
import pandas as pd
import os

from backend.services.allocation_service import allocate_bandwidth


# ============================================================
# CREATE BLUEPRINT
# ============================================================

bandwidth_bp = Blueprint(
    "bandwidth",
    __name__
)


# ============================================================
# HEALTH CHECK
# ============================================================

@bandwidth_bp.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({
        "status": "healthy",
        "service": "smart-wifi-bandwidth-sharing"
    }), 200


# ============================================================
# BANDWIDTH ALLOCATION
# ============================================================

@bandwidth_bp.route(
    "/allocate",
    methods=["POST"]
)
def allocate():

    try:

        # ----------------------------------------------------
        # Get request data
        # ----------------------------------------------------

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "status": "error",
                "message": "Request body is empty"
            }), 400


        # ----------------------------------------------------
        # Get total available bandwidth
        # ----------------------------------------------------

        total_bandwidth = float(
            data.get(
                "total_bandwidth",
                40
            )
        )


        # ----------------------------------------------------
        # Validate bandwidth
        # ----------------------------------------------------

        if total_bandwidth <= 0:

            return jsonify({
                "status": "error",
                "message":
                    "Total bandwidth must be greater than 0"
            }), 400


        # ====================================================
        # GET USERS
        # ====================================================
        #
        # Priority:
        #
        # 1. Users sent by frontend
        # 2. processed_users.csv as fallback
        #
        # This means:
        #
        # 3 users entered in UI
        #       ↓
        # allocation for 3 users
        #
        # No users supplied
        #       ↓
        # use processed_users.csv
        #
        # ====================================================

        users = data.get("users")


        # ====================================================
        # CASE 1: FRONTEND PROVIDED USERS
        # ====================================================

        if users:

            if not isinstance(users, list):

                return jsonify({

                    "status": "error",

                    "message":
                        "Users must be provided as a list"

                }), 400


            # ------------------------------------------------
            # Required fields
            # ------------------------------------------------

            required_fields = [
                "user_id",
                "activity",
                "requested_bandwidth"
            ]


            # ------------------------------------------------
            # Validate each frontend user
            # ------------------------------------------------

            for user in users:

                if not isinstance(user, dict):

                    return jsonify({

                        "status": "error",

                        "message":
                            "Each user must be an object"

                    }), 400


                missing_fields = [

                    field

                    for field in required_fields

                    if field not in user

                ]


                if missing_fields:

                    return jsonify({

                        "status": "error",

                        "message":
                            "User data is missing required fields",

                        "missing_fields":
                            missing_fields

                    }), 400


                # --------------------------------------------
                # Convert requested bandwidth
                # --------------------------------------------

                try:

                    user["requested_bandwidth"] = float(
                        user["requested_bandwidth"]
                    )

                except (TypeError, ValueError):

                    return jsonify({

                        "status": "error",

                        "message":
                            "Invalid requested_bandwidth value",

                        "user_id":
                            user.get("user_id")

                    }), 400


        # ====================================================
        # CASE 2: NO USERS PROVIDED
        # ====================================================

        else:

            # ------------------------------------------------
            # Locate processed dataset
            # ------------------------------------------------

            dataset_path = os.path.join(
                "data",
                "processed_users.csv"
            )


            # ------------------------------------------------
            # Check dataset exists
            # ------------------------------------------------

            if not os.path.exists(dataset_path):

                return jsonify({

                    "status": "error",

                    "message":
                        "No users were provided and processed_users.csv was not found",

                    "expected_path":
                        dataset_path

                }), 404


            # ------------------------------------------------
            # Load processed dataset
            # ------------------------------------------------

            df = pd.read_csv(
                dataset_path
            )


            # ------------------------------------------------
            # Check dataset is not empty
            # ------------------------------------------------

            if df.empty:

                return jsonify({

                    "status": "error",

                    "message":
                        "No users were provided and processed_users.csv is empty"

                }), 400


            # ------------------------------------------------
            # Required dataset columns
            # ------------------------------------------------

            required_fields = [
                "user_id",
                "activity",
                "requested_bandwidth"
            ]


            missing_columns = [

                field

                for field in required_fields

                if field not in df.columns

            ]


            if missing_columns:

                return jsonify({

                    "status": "error",

                    "message":
                        "Dataset is missing required columns",

                    "missing_columns":
                        missing_columns

                }), 400


            # ------------------------------------------------
            # Convert dataframe to users
            # ------------------------------------------------

            users = df.to_dict(
                orient="records"
            )


            # ------------------------------------------------
            # Convert bandwidth values
            # ------------------------------------------------

            for user in users:

                try:

                    user["requested_bandwidth"] = float(
                        user["requested_bandwidth"]
                    )

                except (TypeError, ValueError):

                    return jsonify({

                        "status": "error",

                        "message":
                            "Invalid requested_bandwidth value in dataset",

                        "user_id":
                            user.get("user_id")

                    }), 400


        # ====================================================
        # FINAL USER VALIDATION
        # ====================================================

        if not users:

            return jsonify({

                "status": "error",

                "message":
                    "No users available for allocation"

            }), 400


        # ====================================================
        # RUN GAME THEORY ALLOCATION
        # ====================================================

        result = allocate_bandwidth(

            simulated_users=users,

            total_bandwidth=total_bandwidth

        )


        # ====================================================
        # RETURN RESULT
        # ====================================================

        return jsonify({

            "status": "success",

            "total_bandwidth":
                total_bandwidth,

            "number_of_users":
                len(users),

            "result":
                result

        }), 200


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        return jsonify({

            "status": "error",

            "message":
                "Bandwidth allocation failed",

            "error":
                str(e)

        }), 500