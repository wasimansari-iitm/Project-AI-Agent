# Use a lightweight Python image
FROM python:3.9-slim  

# Set the working directory inside the container
WORKDIR /Project-AI-Agent

# Install system dependencies (combine apt installs for efficiency)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    git \
    ffmpeg \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Prettier globally
RUN npm install -g prettier@3.4.2

# Copy the project files into the working directory
COPY . /Project-AI-Agent  

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000 for the API
EXPOSE 8000

# Start the Flask application
CMD ["python", "app/app.py"]