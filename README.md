NYC Taxi Data Analytics & Prediction Platform
This project implements a complete, end-to-end serverless data platform on AWS to ingest, process, and analyze NYC Taxi trip data. It features an automated Infrastructure as Code (IaC) deployment, a containerized ETL pipeline, and a local data visualization dashboard.

Project Architecture
The architecture consists of the following components:

Data Lake (S3): Two S3 buckets store the raw and processed taxi data in Parquet format.

ETL (Fargate): A Python script, containerized with Docker, runs on AWS Fargate to clean the data, perform feature engineering, and write the processed results back to S3.

Data Catalog (Glue): An AWS Glue crawler (implicitly used by Athena) catalogs the schema of the processed data.

Querying (Athena): Amazon Athena provides a serverless SQL interface to query the processed data directly in S3.

Automation (Terraform & GitHub Actions): The entire cloud infrastructure is defined with Terraform. A GitHub Actions CI/CD pipeline automates the deployment of infrastructure and the building/publishing of the ETL container.

Visualization (Jupyter): A local Jupyter Notebook connects to Athena to run SQL queries and visualizes the results using Python libraries like Matplotlib and Seaborn.

Technology Stack
Cloud Provider: AWS

Infrastructure as Code: Terraform

Data Storage: AWS S3

ETL/Containerization: Python (Pandas), Docker, AWS Fargate

CI/CD: GitHub Actions

Data Querying: AWS Athena

Data Visualization: Python (Jupyter, Matplotlib, Seaborn)

Project Phases
[x] Phase 1: Infrastructure & Ingestion: Deployed foundational AWS resources with Terraform and ingested the first month of raw data.

[x] Phase 2: ETL Containerization: Built a Docker container for the Python processing script and tested it locally.

[x] Phase 3: CI/CD Automation: Created a GitHub Actions workflow to automate infrastructure and container deployment.

[x] Phase 4: Data Analysis: Ran exploratory SQL queries against the processed data using AWS Athena.

[ ] Phase 5: Visualization: Use a local Jupyter Notebook to run Athena queries and create visualizations.

How to Run Locally
Prerequisites: Ensure you have Terraform, Docker, Python 3.9+, and the AWS CLI installed and configured.

Deploy Infrastructure:

cd terraform
terraform init
terraform apply

Run ETL Locally (Optional):

# From project root
docker build -t nyc-taxi-etl .
docker run --rm -v ~/.aws:/root/.aws:ro -v $(pwd)/terraform:/app/terraform:ro nyc-taxi-etl

Run Visualization Notebook:

# From project root
pip install jupyterlab pandas boto3 matplotlib seaborn
jupyter lab

Then, open the analysis.ipynb notebook and run the cells.