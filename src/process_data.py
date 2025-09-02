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

    # In AWS Fargate, credentials and variables will be set via IAM roles.
    # For local execution, we fall back to reading the tfstate file.
    if 'AWS_EXECUTION_ENV' in os.environ:
        # In a real Fargate task, you'd pass these as environment variables
        # For simplicity, we assume the script knows its buckets in a real deployment
        # raw_bucket = os.environ.get('RAW_BUCKET')
        # processed_bucket = os.environ.get('PROCESSED_BUCKET')
        print("Running in cloud environment (Fargate/ECS). Bucket names should be provided via env vars.")
        # This part of the logic would need to be expanded for a production Fargate run
        # For now, we exit if we can't get buckets, as this container is for CI/CD validation.
        return
    else:
        print("Environment variables not set. Falling back to tfstate for local run...")
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
    # --- THIS IS THE CORRECTED LINE ---
    output_path = f's3://{processed_bucket}/trips/{key}' # Write to the 'trips/' subfolder

    print(f"Reading data from: {input_path}")
    df = pd.read_parquet(input_path)

    print("Initial data types:\n", df.dtypes)
    print(f"Initial row count: {len(df)}")

    # 1. Data Cleaning: Drop rows with invalid data
    df = df[(df['trip_distance'] > 0) & (df['fare_amount'] > 0)]
    print(f"Row count after filtering invalid trips: {len(df)}")

    # 2. Feature Engineering: Calculate trip duration in minutes
    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])
    df['trip_duration_minutes'] = (df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']).dt.total_seconds() / 60

    # 3. Data Cleaning: Remove outliers (e.g., trips longer than 2 hours or less than 1 minute)
    df = df[(df['trip_duration_minutes'] >= 1) & (df['trip_duration_minutes'] <= 120)]
    print(f"Row count after filtering duration outliers: {len(df)}")

    # Select only the relevant columns for the final output
    final_columns = [
        'vendorid', 'tpep_pickup_datetime', 'tpep_dropoff_datetime', 'passenger_count',
        'trip_distance', 'ratecodeid', 'pulocationid', 'dolocationid', 'payment_type',
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