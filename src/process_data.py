import pandas as pd
import boto3
import json
import os
from urllib.parse import urlparse

def get_bucket_names_from_tfstate(tfstate_path='terraform/terraform.tfstate'):
    """Reads bucket names from the Terraform state file."""
    try:
        with open(tfstate_path, 'r') as f:
            tfstate = json.load(f)
        
        raw_bucket = tfstate['outputs']['raw_data_bucket_name']['value']
        processed_bucket = tfstate['outputs']['processed_data_bucket_name']['value']
        return raw_bucket, processed_bucket
    except (FileNotFoundError, KeyError) as e:
        print(f"Error reading Terraform state file: {e}")
        return None, None

def main():
    """
    Main ETL function to process taxi data.
    - Reads raw data from S3.
    - Cleans and transforms the data.
    - Writes processed data back to a different S3 location.
    """
    raw_bucket, processed_bucket = None, None

    # For local execution, we fall back to reading the tfstate file.
    print("Falling back to tfstate for local run...")
    raw_bucket, processed_bucket = get_bucket_names_from_tfstate()

    if not raw_bucket or not processed_bucket:
        print("Could not determine bucket names. Exiting.")
        return

    # Use boto3 to find the latest object in the raw bucket
    s3 = boto3.client('s3')
    objects = s3.list_objects_v2(Bucket=raw_bucket).get('Contents', [])
    if not objects:
        print(f"No objects found in raw bucket: {raw_bucket}")
        return
    
    latest_object = max(objects, key=lambda x: x['LastModified'])
    key = latest_object['Key']
    
    input_path = f's3://{raw_bucket}/{key}'
    output_path = f's3://{processed_bucket}/trips/{os.path.basename(key)}'

    print(f"Reading data from: {input_path}")
    df = pd.read_parquet(input_path)

    print(f"Initial row count: {len(df)}")

    # 1. Data Cleaning: Drop rows with invalid data
    df = df[(df['trip_distance'] > 0) & (df['fare_amount'] > 0)]
    print(f"Row count after filtering invalid trips: {len(df)}")

    # 2. Feature Engineering: Calculate trip duration in minutes
    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])
    df['trip_duration_minutes'] = (df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']).dt.total_seconds() / 60

    # 3. Data Cleaning: Remove outliers
    df = df[(df['trip_duration_minutes'] >= 1) & (df['trip_duration_minutes'] <= 120)]
    print(f"Row count after filtering duration outliers: {len(df)}")

    # --- THIS IS THE CORRECTED LIST OF COLUMNS ---
    # Select only the relevant columns using their correct, case-sensitive names.
    final_columns = [
        'VendorID', 'tpep_pickup_datetime', 'tpep_dropoff_datetime', 'passenger_count',
        'trip_distance', 'RatecodeID', 'PULocationID', 'DOLocationID', 'payment_type',
        'fare_amount', 'extra', 'mta_tax', 'tip_amount', 'tolls_amount',
        'improvement_surcharge', 'total_amount', 'congestion_surcharge', 'airport_fee',
        'trip_duration_minutes'
    ]
    # Filter out any columns that might not exist in older datasets
    df_final = df[[col for col in final_columns if col in df.columns]]
    
    print(f"Writing processed data to: {output_path}")
    df_final.to_parquet(output_path, index=False)
    
    print("ETL process complete.")

if __name__ == "__main__":
    main()