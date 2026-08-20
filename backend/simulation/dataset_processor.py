import pandas as pd
import os

import numpy as np


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

INPUT_FILE = os.path.join(
    DATA_DIR,
    "Cleaned_Dataset.csv"
)

OUTPUT_FILE = os.path.join(
    DATA_DIR,
    "processed_users.csv"
)


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset():

    df = pd.read_csv(
        INPUT_FILE
    )

    required_columns = [
        "time",
        "source",
        "protocol",
        "length"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    return df

def load_processed_users():
    return pd.read_csv(OUTPUT_FILE).to_dict(orient="records")
# ============================================================
# CLEAN BASIC VALUES
# ============================================================

def clean_dataset(df):

    df = df.copy()

    # Remove rows without a source
    df = df.dropna(
        subset=["source"]
    )

    # Remove invalid packet sizes
    df = df[
        df["length"] > 0
    ]

    # Remove invalid timestamps
    df = df[
        df["time"] >= 0
    ]

    # Make sure packet length is numeric
    df["length"] = pd.to_numeric(
        df["length"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["length"]
    )

    return df


# ============================================================
# CALCULATE TRAFFIC PER USER
# ============================================================

def calculate_user_traffic(df):

    start_time = df["time"].min()

    end_time = df["time"].max()

    duration = end_time - start_time

    if duration <= 0:

        raise ValueError(
            "Dataset duration must be greater than zero."
        )


    grouped = (
        df
        .groupby("source")
        .agg(

            total_bytes=(
                "length",
                "sum"
            ),

            packet_count=(
                "length",
                "count"
            ),

            active_protocols=(
                "protocol",
                "nunique"
            )

        )
        .reset_index()
    )


    # --------------------------------------------------------
    # Average bandwidth
    #
    # bytes -> bits -> Mbps
    # --------------------------------------------------------

    grouped["requested_bandwidth"] = (

        grouped["total_bytes"]
        * 8
        / duration
        / 1_000_000

    )


    return grouped


# ============================================================
# ASSIGN MODELED ACTIVITY
# ============================================================

def assign_activity(df):

    df = df.copy()

    bandwidth = (
        df["requested_bandwidth"]
    )


    # --------------------------------------------------------
    # Use traffic demand to create a simple modeled activity
    # category.
    #
    # IMPORTANT:
    # These activities are NOT directly observed in the
    # packet dataset. They are modeling assumptions for the
    # Game Theory simulation.
    # --------------------------------------------------------

    conditions = [

        bandwidth >= 2.0,

        bandwidth >= 0.5,

        bandwidth < 0.5

    ]

    choices = [

        "streaming",

        "gaming",

        "web"

    ]


    df["activity"] = np.select(

        conditions,

        choices,

        default="web"

    )


    return df


# ============================================================
# CREATE PROJECT DATASET
# ============================================================

def create_project_dataset():

    print(
        "Loading cleaned dataset..."
    )

    df = load_dataset()


    print(
        f"Original rows: {len(df)}"
    )


    df = clean_dataset(
        df
    )


    print(
        f"Rows after cleaning: {len(df)}"
    )


    traffic = calculate_user_traffic(
        df
    )


    traffic = assign_activity(
        traffic
    )


    # --------------------------------------------------------
    # Create project user IDs
    # --------------------------------------------------------

    traffic["user_id"] = [

        f"user_{i:03d}"

        for i in range(
            1,
            len(traffic) + 1
        )

    ]


    # --------------------------------------------------------
    # Keep only fields required by Game Theory
    # --------------------------------------------------------

    result = traffic[
        [
            "user_id",
            "activity",
            "requested_bandwidth"
        ]
    ].copy()


    # --------------------------------------------------------
    # Round bandwidth
    # --------------------------------------------------------

    result["requested_bandwidth"] = (

        result["requested_bandwidth"]
        .round(4)

    )


    # --------------------------------------------------------
    # Remove zero-demand users
    # --------------------------------------------------------

    result = result[
        result["requested_bandwidth"] > 0
    ]


    # --------------------------------------------------------
    # Save processed dataset
    # --------------------------------------------------------

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )


    print()
    print(
        "======================================"
    )
    print(
        " DATASET PROCESSING COMPLETE"
    )
    print(
        "======================================"
    )

    print(
        f"Users created: {len(result)}"
    )

    print(
        f"Output file: {OUTPUT_FILE}"
    )

    print()
    print(
        result.head(10)
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    create_project_dataset()