# Use an official Python runtime as a parent image.
# This provides a lean Linux environment with Python pre-installed.
FROM python:3.9-slim

# Set the working directory inside the container to /app.
# All subsequent commands (COPY, RUN) will be relative to this path.
WORKDIR /app

# Copy the file that lists our Python dependencies into the container.
COPY requirements.txt .

# Install the dependencies listed in requirements.txt.
# The --no-cache-dir option is a good practice to keep the image size small.
RUN pip install --no-cache-dir -r requirements.txt

# Copy our source code (the contents of the local src/ folder)
# into the container's /app/src directory.
COPY src/ ./src/

# Specify the command to run when the container starts.
# This will execute our main ETL script.
CMD ["python", "src/process_data.py"]
