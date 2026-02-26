FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

# Copy application code
COPY . .

# Entrypoint script
COPY start.sh .
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Run the application (API + Worker + Beat)
CMD ["./start.sh"]
