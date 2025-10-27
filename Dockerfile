FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-railway.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-railway.txt

# Copy the application
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "simple_app.py"]
