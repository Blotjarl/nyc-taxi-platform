# src/ingest_data.py
# This script downloads a single month of NYC taxi data and uploads it to S3.

import requests
import boto3
import os

# --- Configuration ---
# URL for the Yellow Taxi data for January 2024.
# The NYC TLC website provides these URLs.
DATA_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
LOCAL_FILENAME = "yellow_tripdata_2024-01.parquet"

def get_raw_bucket_name():
    """
    Gets the name of the raw data S3 bucket from Terraform outputs.
    This is a robust way to avoid hardcoding the bucket name.
    """
    # NOTE: This assumes you run the script from the project's root directory.
    try:
        # CORRECTED PATH: Look in the 'terraform' sub-directory from our current location.
        with open("terraform/terraform.tfstate") as f:
            import json
            state = json.load(f)
            return state['outputs']['raw_data_bucket_name']['value']
    except Exception as e:
        print(f"Error reading Terraform state file: {e}")
        print("Please ensure you have run 'terraform apply' in the 'terraform' directory.")
        print("You can also hardcode the bucket name as a fallback.")
        return None # Or return a hardcoded bucket name for testing

def download_data(url, filename):
    """Downloads a file from a URL to a local path."""
    if os.path.exists(filename):
        print(f"File {filename} already exists. Skipping download.")
        return True
    
    print(f"Downloading data from {url} to {filename}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading data: {e}")
        return False

def upload_to_s3(local_file, bucket_name, s3_key):
    """Uploads a local file to an S3 bucket."""
    s3 = boto3.client('s3')
    print(f"Uploading {local_file} to S3 bucket {bucket_name} as {s3_key}...")
    try:
        s3.upload_file(local_file, bucket_name, s3_key)
        print("Upload to S3 complete.")
    except Exception as e:
        print(f"Error uploading to S3: {e}")

def main():
    """Main function to run the ingestion process."""
    # Get the S3 bucket name from Terraform state
    raw_bucket_name = get_raw_bucket_name()
    if not raw_bucket_name:
        return # Exit if we couldn't get the bucket name

    # Step 1: Download the data file locally
    if download_data(DATA_URL, LOCAL_FILENAME):
        # Step 2: Upload the file to S3
        upload_to_s3(LOCAL_FILENAME, raw_bucket_name, LOCAL_FILENAME)
        
        # Optional: Clean up the local file after upload
        # os.remove(LOCAL_FILENAME)
        # print(f"Removed local file: {LOCAL_FILENAME}")

if __name__ == "__main__":
    main()

