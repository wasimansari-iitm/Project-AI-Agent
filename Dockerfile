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
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ensure the environment variables are loaded at runtime
ENV PYTHONUNBUFFERED=1

# Create the /data directory inside the container
COPY data /data
RUN chmod 777 /data

USER appuser

# Expose port 8000 for the API
EXPOSE 8000

# Entrypoint with token validation

# Ensure AIPROXY_TOKEN is set and set DATA_DIR correctly
CMD ["sh", "-c", \
    "if [ -z \"$AIPROXY_TOKEN\" ]; then \
        echo 'ERROR: Please set AIPROXY_TOKEN via -e flag' to access the app >&2; \
        exit 1; \
    fi; \
    DATA_DIR=/data PYTHONUNBUFFERED=1 exec python app.py"]