FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only necessary files
COPY requirements.txt config.yaml ./  
COPY tws/ ./tws/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the entrypoint
ENTRYPOINT ["python", "tws/main.py"]
