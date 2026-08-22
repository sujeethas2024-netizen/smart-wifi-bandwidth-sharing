import os
import pandas as pd

# Find Cleaned_Dataset.csv inside data/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASET_PATH = os.path.join(BASE_DIR, 'data', 'Cleaned_Dataset.csv')

def get_cleaned_data():
    """Loads and returns the cleaned dataframe."""
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset file not found at: {DATASET_PATH}")
    return pd.read_csv(DATASET_PATH)

def get_dataset_records(limit=100):
    """Returns dataset rows as a list of dictionaries."""
    df = get_cleaned_data()
    return df.head(limit).to_dict(orient='records')
    