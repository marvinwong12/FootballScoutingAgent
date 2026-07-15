FROM python:3.13-slim

WORKDIR /app

# Install basic compiler flags if ChromaDB or some dependencies need compiling
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies first to cache this layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY . .

# Keep the container running or set tests as default
CMD ["pytest", "tests/"]