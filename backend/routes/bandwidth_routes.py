from flask import Blueprint, request, jsonify
import math
import pandas as pd
import os

from backend.services.allocation_service import allocate_bandwidth
from backend.services.live_allocation_service import build_live_allocation_request
from backend.simulation.experiment_runner import run_experiment_json, get_experiment_config
from backend.data_provenance import SIMULATION, CALCULATED_FROM_REAL_DATA, REAL_USER_INPUT, RESEARCH_SIMULATION
from backend.experiments.config_schema import ExperimentConfig
from backend.experiments.runner import run_multi_seed_experiment
from backend.experiments.ablation import run_ablation
from backend.experiments.sensitivity import run_sensitivity_analysis
from backend.experiments.report import generate_report

from backend.database.accounts_db import (
    get_live_session,
    live_session_status,
    LIVE_SESSION_STATUS_ACTIVE,
)


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

        # ---- Authentication: require a valid live session ----
        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
            return jsonify({
                "status": "error",
                "message": "Missing or malformed Authorization header.",
            }), 401
        session_id = parts[1].strip()
        session_row = get_live_session(session_id)
        if not session_row:
            return jsonify({
                "status": "error",
                "message": "Invalid session.",
            }), 401
        if live_session_status(session_row) != LIVE_SESSION_STATUS_ACTIVE:
            return jsonify({
                "status": "error",
                "message": "Session is not active.",
            }), 401

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "status": "error",
                "message": "Request body is empty"
            }), 400


        # If the caller asks for a LIVE allocation, derive the user list
        # from the server-authoritative active-session table so the
        # backend never trusts a client-supplied user population.
        # Real bandwidth requests must come from the client via
        # ``user_requests``; users without a real request are excluded.
        use_live_users = bool(data.get("use_live_users"))
        user_requests = data.get("user_requests") or {}

        if use_live_users and user_requests:
            for username, requested in user_requests.items():
                try:
                    value = float(requested)
                except (TypeError, ValueError):
                    return jsonify({
                        "status": "error",
                        "message": (
                            f"Invalid requested_bandwidth for user '{username}': "
                            "value must be a positive finite number."
                        ),
                    }), 400
                if value <= 0 or not math.isfinite(value):
                    return jsonify({
                        "status": "error",
                        "message": (
                            f"Invalid requested_bandwidth for user '{username}': "
                            "value must be a positive finite number."
                        ),
                    }), 400

        if use_live_users:
            live_users, live_meta = build_live_allocation_request(
                total_bandwidth=float(data.get("total_bandwidth", 40.0)),
                user_requests=user_requests,
            )
            if not live_users:
                return jsonify({
                    "status": "error",
                    "message": (
                        "No active live users with a bandwidth request. "
                        "Each active user must provide a requested_bandwidth."
                    ),
                    "source": "live_sessions",
                }), 400
            data = dict(data)
            data["users"] = live_users
            data["_live_source"] = live_meta

        total_bandwidth = float(
            data.get(
                "total_bandwidth",
                40
            )
        )


        if total_bandwidth <= 0:

            return jsonify({
                "status": "error",
                "message":
                    "Total bandwidth must be greater than 0"
            }), 400


        users = data.get("users")


        if users:

            if not isinstance(users, list):

                return jsonify({

                    "status": "error",

                    "message":
                        "Users must be provided as a list"

                }), 400


            required_fields = [
                "user_id",
                "activity",
                "requested_bandwidth"
            ]


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


        else:

            dataset_path = os.path.join(
                "data",
                "processed_users.csv"
            )


            if not os.path.exists(dataset_path):

                return jsonify({

                    "status": "error",

                    "message":
                        "No users were provided and processed_users.csv was not found",

                    "expected_path":
                        dataset_path

                }), 404


            df = pd.read_csv(
                dataset_path
            )


            if df.empty:

                return jsonify({

                    "status": "error",

                    "message":
                        "No users were provided and processed_users.csv is empty"

                }), 400


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


            users = df.to_dict(
                orient="records"
            )


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


        if not users:

            return jsonify({

                "status": "error",

                "message":
                    "No users available for allocation"

            }), 400


        result = allocate_bandwidth(

            simulated_users=users,

            total_bandwidth=total_bandwidth

        )


        return jsonify({

            "status": "success",

            "source": CALCULATED_FROM_REAL_DATA,

            "provenance": {
                "user_demand": REAL_USER_INPUT,
                "allocation": CALCULATED_FROM_REAL_DATA,
                "metrics": CALCULATED_FROM_REAL_DATA,
                "fairness": CALCULATED_FROM_REAL_DATA,
            },

            "total_bandwidth":
                total_bandwidth,

            "number_of_users":
                len(users),

            "live_source": data.get("_live_source"),

            "result":
                result

        }), 200


    except Exception as e:

        return jsonify({

            "status": "error",

            "message":
                "Bandwidth allocation failed",

            "error":
                str(e)

        }), 500


# ============================================================
# EXPERIMENT RUNNER API
# ============================================================

@bandwidth_bp.route("/experiment/run", methods=["POST"])
def run_experiment():
    try:
        data = request.get_json(silent=True) or {}

        user_counts = data.get("user_counts")
        total_bandwidth = data.get("total_bandwidth")
        seed = data.get("seed")

        if user_counts is not None:
            if not isinstance(user_counts, list) or len(user_counts) == 0:
                return jsonify({
                    "status": "error",
                    "message": "user_counts must be a non-empty list of integers",
                }), 400
            user_counts = [int(c) for c in user_counts]

        if total_bandwidth is not None:
            total_bandwidth = float(total_bandwidth)
            if total_bandwidth <= 0:
                return jsonify({
                    "status": "error",
                    "message": "total_bandwidth must be greater than 0",
                }), 400

        if seed is not None:
            seed = int(seed)

        experiment_data = run_experiment_json(
            user_counts=user_counts,
        )

        if total_bandwidth is not None:
            experiment_data["config"]["total_bandwidth"] = total_bandwidth
        if seed is not None:
            experiment_data["config"]["seed"] = seed

        return jsonify({
            "status": "success",
            "source": CALCULATED_FROM_REAL_DATA,
            "data_source": "Synthetic traffic scenarios + Game Theory engine",
            "provenance": {
                "user_demand": "SIMULATION (synthetic traffic generator)",
                "allocation": CALCULATED_FROM_REAL_DATA,
                "metrics": CALCULATED_FROM_REAL_DATA,
                "fairness": CALCULATED_FROM_REAL_DATA,
                "note": (
                    "User demands are synthetically generated for scalability testing. "
                    "For real dataset demands, use processed_users.csv with /api/allocate."
                ),
            },
            **experiment_data,
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Experiment failed",
            "error": str(e),
        }), 500


@bandwidth_bp.route("/experiment/config", methods=["GET"])
def get_experiment_config_endpoint():
    config = get_experiment_config()
    return jsonify({
        "status": "success",
        "config": config,
    }), 200


# ============================================================
# MULTI-SEED EXPERIMENT API
# ============================================================

@bandwidth_bp.route("/experiment/run-multi-seed", methods=["POST"])
def run_multi_seed_experiment_endpoint():
    try:
        data = request.get_json(silent=True) or {}

        config = ExperimentConfig(
            seed=data.get("seed", 42),
            repetitions=data.get("repetitions", 30),
            user_counts=data.get("user_counts", [5, 10, 20, 30, 50, 100, 200, 373]),
            total_bandwidth=data.get("total_bandwidth", 100.0),
            scenario=data.get("scenario", "medium"),
            algorithms=data.get("algorithms", [
                "equal", "proportional", "priority", "max_min_fairness", "alpha_fair", "game_theory"
            ]),
        )

        result = run_multi_seed_experiment(config)

        return jsonify({
            "status": "success",
            "source": CALCULATED_FROM_REAL_DATA,
            "data_source": "Synthetic traffic scenarios + multi-seed experiment engine",
            "provenance": {
                "user_demand": SIMULATION,
                "allocation": CALCULATED_FROM_REAL_DATA,
                "metrics": CALCULATED_FROM_REAL_DATA,
                "fairness": CALCULATED_FROM_REAL_DATA,
                "statistics": CALCULATED_FROM_REAL_DATA,
                "note": (
                    "Multi-seed experiment with " + str(config.repetitions) + " repetitions per configuration. "
                    "Raw results stored in data/raw_results.csv. Aggregated statistics in data/aggregated_results.csv."
                ),
            },
            **result,
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Multi-seed experiment failed",
            "error": str(e),
        }), 500


# ============================================================
# ABLATION STUDY API
# ============================================================

@bandwidth_bp.route("/experiment/ablation", methods=["POST"])
def run_ablation_experiment():
    try:
        data = request.get_json(silent=True) or {}

        config = ExperimentConfig(
            seed=data.get("seed", 42),
            repetitions=data.get("repetitions", 10),
            user_counts=data.get("user_counts", [10, 50, 100]),
            total_bandwidth=data.get("total_bandwidth", 100.0),
            scenario=data.get("scenario", "medium"),
            algorithms=data.get("algorithms", ["game_theory"]),
        )

        result = run_ablation(config)

        return jsonify({
            "status": "success",
            "source": CALCULATED_FROM_REAL_DATA,
            "provenance": {
                "user_demand": SIMULATION,
                "allocation": CALCULATED_FROM_REAL_DATA,
                "metrics": CALCULATED_FROM_REAL_DATA,
                "note": "Ablation study with individual utility components removed.",
            },
            **result,
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Ablation study failed",
            "error": str(e),
        }), 500


# ============================================================
# SENSITIVITY ANALYSIS API
# ============================================================

@bandwidth_bp.route("/experiment/sensitivity", methods=["POST"])
def run_sensitivity_experiment():
    try:
        data = request.get_json(silent=True) or {}

        parameter = data.get("parameter", "w_throughput")
        values = data.get("values", [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0])

        base_config = ExperimentConfig(
            seed=data.get("seed", 42),
            repetitions=data.get("repetitions", 10),
            user_counts=data.get("user_counts", [10, 50, 100]),
            total_bandwidth=data.get("total_bandwidth", 100.0),
            scenario=data.get("scenario", "medium"),
            algorithms=data.get("algorithms", ["game_theory"]),
        )

        result = run_sensitivity_analysis(base_config, parameter, values)

        return jsonify({
            "status": "success",
            "source": CALCULATED_FROM_REAL_DATA,
            "provenance": {
                "user_demand": SIMULATION,
                "allocation": CALCULATED_FROM_REAL_DATA,
                "metrics": CALCULATED_FROM_REAL_DATA,
                "note": f"Sensitivity analysis varying {parameter} across {len(values)} values.",
            },
            **result,
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Sensitivity analysis failed",
            "error": str(e),
        }), 500


# ============================================================
# REPORT GENERATION API
# ============================================================

@bandwidth_bp.route("/experiment/report", methods=["GET", "POST"])
def get_experiment_report():
    try:
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            experiment_result = data.get("experiment_result", {})
            statistics_results = data.get("statistics_results")
            ablation_results = data.get("ablation_results")
            sensitivity_results = data.get("sensitivity_results")
            output_directory = data.get("output_directory", "data")
        else:
            experiment_result = {}
            statistics_results = None
            ablation_results = None
            sensitivity_results = None
            output_directory = "data"

        if experiment_result:
            os.makedirs(output_directory, exist_ok=True)
            from backend.experiments.runner import (
                save_raw_results,
                save_aggregated_results,
                save_experiment_config,
            )
            raw = experiment_result.get("raw_results", [])
            agg = experiment_result.get("aggregated_results", [])
            config_dict = experiment_result.get("config", {})
            config = ExperimentConfig.from_dict(config_dict)
            save_raw_results(raw, output_directory)
            save_aggregated_results(agg, output_directory)
            save_experiment_config(config, output_directory)

            if statistics_results:
                with open(os.path.join(output_directory, "statistics_results.json"), "w", encoding="utf-8") as f:
                    import json
                    json.dump(statistics_results, f, indent=2)
            if ablation_results:
                with open(os.path.join(output_directory, "ablation_results.json"), "w", encoding="utf-8") as f:
                    import json
                    json.dump(ablation_results, f, indent=2)
            if sensitivity_results:
                with open(os.path.join(output_directory, "sensitivity_results.json"), "w", encoding="utf-8") as f:
                    import json
                    json.dump(sensitivity_results, f, indent=2)

        report_config = ExperimentConfig.from_dict(
            {"output_directory": output_directory}
        )
        report_data = generate_report(config=report_config)

        if report_data.get("report_path"):
            markdown = report_data.get("markdown")
            return jsonify({
                "status": "success",
                "report_path": report_data["report_path"],
                "report": markdown,
                "report_content": markdown,
                "provenance": report_data.get("provenance"),
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Report generation failed",
            }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Report generation failed",
            "error": str(e),
        }), 500


# ============================================================
# RESEARCH RESULTS API — serves existing processed dataset
# ============================================================

@bandwidth_bp.route("/experiment/results", methods=["GET"])
def get_experiment_results():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        agg_path = os.path.join(base_dir, "data", "aggregated_results.csv")
        raw_path = os.path.join(base_dir, "data", "raw_results.csv")

        result = {
            "status": "success",
            "source": RESEARCH_SIMULATION,
            "provenance": {
                "user_demand": SIMULATION,
                "allocation": CALCULATED_FROM_REAL_DATA,
                "metrics": CALCULATED_FROM_REAL_DATA,
                "fairness": CALCULATED_FROM_REAL_DATA,
                "note": (
                    "Controlled research dataset. "
                    "Raw results: data/raw_results.csv. "
                    "Aggregated results: data/aggregated_results.csv."
                ),
            },
        }

        if os.path.exists(agg_path):
            df = pd.read_csv(agg_path)
            result["aggregated"] = df.to_dict(orient="records")
            result["aggregated_count"] = len(df)
        else:
            result["aggregated"] = []
            result["aggregated_count"] = 0

        if os.path.exists(raw_path):
            df = pd.read_csv(raw_path)
            result["raw"] = df.to_dict(orient="records")
            result["raw_count"] = len(df)
        else:
            result["raw"] = []
            result["raw_count"] = 0

        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Failed to load research results",
            "error": str(e),
        }), 500
