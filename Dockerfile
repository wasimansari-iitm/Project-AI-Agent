# Use lightweight Python image
FROM python:3.9-slim  

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*  # Clean up to reduce image size

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose the port for Flask API
EXPOSE 8000

# Run the Flask application
CMD ["python", "app.py"]