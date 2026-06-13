FROM python:3.10-slim

# Install system dependencies, including redis-server and postgresql-client
RUN apt-get update && apt-get install -y \
    redis-server \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project code
COPY . .

# Expose port 7860 (Hugging Face Spaces default port)
EXPOSE 7860

# Make start script executable and convert line endings if necessary
RUN chmod +x start.sh && sed -i 's/\r$//' start.sh

CMD ["./start.sh"]
