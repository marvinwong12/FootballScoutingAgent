FROM python:3.13-slim

WORKDIR /app

# 1. Install build tools, run compilation, and CLEAN UP the package manager list in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. Tell pip to download the lightweight, CPU-ONLY version of PyTorch first!
# This single change shrinks your image size by over 1.5 GB.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 3. Copy and install rest of dependencies (without storing cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Clean up compiler tools to shave off an extra 100MB+ (Optional but great for production)
RUN apt-get purge -y --auto-remove build-essential

# Copy source code
COPY . .

CMD ["pytest", "tests/"]