import pandas as pd

# 1. Define File Paths (Notice the 'r' before quotes to handle Windows path slashes)
input_path = r"C:\Users\Lenovo\OneDrive\Documents\game theroy project\Dataset.csv"
output_path = r"C:\Users\Lenovo\OneDrive\Documents\game theroy project\Cleaned_Dataset.csv"

print("--- 1. LOADING DATASET ---")
df = pd.read_csv(input_path)
print(f"Initial Shape: {df.shape[0]} rows, {df.shape[1]} columns\n")

print("--- 2. BEFORE CLEANING STATS ---")
print(f"Duplicate Rows Found: {df.duplicated().sum()}")
print("Missing Values Count Per Column:")
print(df.isnull().sum())
print("\n" + "="*50 + "\n")

# --- 3. DATA CLEANING OPERATIONS ---
# A. Standardize column names (removes spaces, lowercase, replaces spaces with underscores)
df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

# B. Remove duplicate rows
df = df.drop_duplicates()

# C. Fill missing numeric values with the column median
numeric_cols = df.select_dtypes(include=['number']).columns
df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

# D. Fill missing text/categorical values with 'unknown'
text_cols = df.select_dtypes(include=['object']).columns
df[text_cols] = df[text_cols].fillna('unknown')

# --- 4. VERIFICATION CHECK (HOW TO KNOW IT IS CLEAN) ---
total_duplicates = df.duplicated().sum()
total_missing = df.isnull().sum().sum()

print("--- 5. AFTER CLEANING VERIFICATION REPORT ---")
print(f"Final Shape: {df.shape[0]} rows, {df.shape[1]} columns")
print(f"Remaining Duplicate Rows: {total_duplicates}")
print(f"Remaining Missing Values: {total_missing}")

print("\nColumn-by-Column Missing Value Check:")
print(df.isnull().sum())

print("\nCleaned Column Names:")
print(list(df.columns))

print("\nFirst 5 Rows Preview:")
print(df.head())

print("\n" + "="*50)
# Final Verdict Check
if total_duplicates == 0 and total_missing == 0:
    print("VERDICT: SUCCESS! YOUR DATASET IS 100% CLEAN.")
else:
    print("VERDICT: WARNING! Some missing values or issues remain.")

# Save the cleaned data to a new file
df.to_csv(output_path, index=False)
print(f"\nCleaned file saved as: {output_path}")