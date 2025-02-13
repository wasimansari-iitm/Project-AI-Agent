# Use an official Python runtime as a base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy only requirements.txt first (to cache dependencies)
COPY requirements.txt /app/

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the project files
COPY . /app/

# Expose port 8000 for the application
EXPOSE 8000

# Command to run the application
CMD ["python", "app.py"]