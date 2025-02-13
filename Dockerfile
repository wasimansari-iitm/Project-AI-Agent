# Use a lightweight Python image
FROM python:3.9-slim  

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the contents of the 'app' folder into the working directory
COPY app/ .  

# Expose port 8000 for the API
EXPOSE 8000

# Start the Flask application
CMD ["python", "app.py"]