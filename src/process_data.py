# src/process_data.py
# This script runs inside the Fargate container.
# It reads raw data from S3, cleans it, and writes processed data back to S3.

import os
import boto3
import pandas as pd

def get_bucket_names():
    """
    Gets the S3 bucket names from environment variables set by Terraform/Fargate.
    This is more robust than reading the tfstate file inside a container.
    """
    # In a real Fargate task, you would pass these as environment variables.
    # For local testing, we fall back to reading the state file.
    raw_bucket = os.environ.get('RAW_BUCKET_NAME')
    processed_bucket = os.environ.get('PROCESSED_BUCKET_NAME')

    if raw_bucket and processed_bucket:
        return raw_bucket, processed_bucket

    print("Environment variables not set. Falling back to tfstate for local run...")
    try:
        with open("terraform/terraform.tfstate") as f:
            import json
            state = json.load(f)
            raw_bucket = state['outputs']['raw_data_bucket_name']['value']
            processed_bucket = state['outputs']['processed_data_bucket_name']['value']
            return raw_bucket, processed_bucket
    except Exception as e:
        print(f"Error reading Terraform state file: {e}")
        return None, None

def main():
    """Main ETL logic function."""
    raw_bucket, processed_bucket = get_bucket_names()
    if not raw_bucket or not processed_bucket:
        print("Could not determine bucket names. Exiting.")
        return

    # For this example, we process a specific file.
    # A more advanced version would list all files in the raw bucket.
    input_key = "yellow_tripdata_2024-01.parquet"
    output_key = "processed_yellow_tripdata_2024-01.parquet"

    input_path = f"s3://{raw_bucket}/{input_key}"
    output_path = f"s3://{processed_bucket}/{output_key}"

    print(f"Reading data from: {input_path}")
    df = pd.read_parquet(input_path)
    
    print("Initial data types:\n", df.dtypes)
    print(f"Initial row count: {len(df)}")

    # --- 1. Data Cleaning and Transformation ---
    
    # Convert pickup and dropoff times to datetime objects
    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])

    # Remove trips with no passengers or zero trip distance, as they are likely errors
    df = df[(df['passenger_count'] > 0) & (df['trip_distance'] > 0)]
    print(f"Row count after filtering invalid trips: {len(df)}")

    # --- 2. Feature Engineering ---

    # Calculate trip duration in minutes. This will be our prediction target.
    duration = df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']
    df['trip_duration_minutes'] = duration.dt.total_seconds() / 60

    # Filter out extreme outliers for trip duration (e.g., trips lasting > 2 hours)
    df = df[(df['trip_duration_minutes'] >= 1) & (df['trip_duration_minutes'] <= 120)]
    print(f"Row count after filtering duration outliers: {len(df)}")

    # --- 3. Write Processed Data to S3 ---
    
    print(f"Writing processed data to: {output_path}")
    df.to_parquet(output_path, index=False)
    
    print("ETL process complete.")

if __name__ == "__main__":
    main()
