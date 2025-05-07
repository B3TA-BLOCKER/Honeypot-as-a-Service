# Use official Ubuntu base image
FROM ubuntu:20.04

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    docker.io \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install application dependencies (e.g., Flask)
COPY requirements.txt /app/
RUN pip3 install -r /app/requirements.txt

# Copy application files to container
COPY . /app/

# Expose the port the app runs on
EXPOSE 80

# Run the application
CMD ["python3", "/app/webapp/app.py"]

