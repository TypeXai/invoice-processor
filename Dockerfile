FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MAX_CONTENT_LENGTH=6291456 \
    GEMINI_TIMEOUT=30 \
    TOTAL_REQUEST_TIMEOUT=35 \
    PORT=8080

# Add health check endpoint
RUN echo 'from flask import jsonify\n\
@app.route("/health")\n\
def health_check():\n\
    return jsonify({"status": "healthy"}), 200' >> app.py

# Expose port
EXPOSE 8080

# Run with gunicorn
CMD exec gunicorn --bind :$PORT --workers 4 --timeout 120 --access-logfile - --error-logfile - --log-level info app:app 