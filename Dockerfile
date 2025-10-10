# ===============================================================
# 1. Base image
# ===============================================================
FROM python:3.11-slim

# ---------------------------------------------------------------
# 2. Install system dependencies (Google Chrome + fonts)
# ---------------------------------------------------------------
RUN apt-get update && \
    apt-get install -y wget gnupg ca-certificates fonts-liberation libnss3 && \
    mkdir -p /etc/apt/keyrings && \
    wget -q -O /etc/apt/keyrings/google-linux-signing-key.gpg https://dl.google.com/linux/linux_signing_key.pub && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-linux-signing-key.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
        > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------
# 3. Working directory
# ---------------------------------------------------------------
WORKDIR /app

# ---------------------------------------------------------------
# 4. Copy dependencies and install Python packages
# ---------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------
# 5. Copy project files
# ---------------------------------------------------------------
COPY . .

# ---------------------------------------------------------------
# 6. Expose port (FastAPI + Flet share same app)
# ---------------------------------------------------------------
EXPOSE 8000

# ---------------------------------------------------------------
# 7. Environment variables (Railway injects these automatically)
# ---------------------------------------------------------------
ENV PYTHONUNBUFFERED=1 \
    PATH="/usr/bin/google-chrome:$PATH" \
    SUPABASE_URL=${SUPABASE_URL} \
    SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY} \
    MAPBOX_TOKEN=${MAPBOX_TOKEN} \
    API_URL=${API_URL}

# ---------------------------------------------------------------
# 8. Verify Chrome installation (optional)
# ---------------------------------------------------------------
RUN google-chrome --version || echo "⚠️ Chrome not found!"

# ---------------------------------------------------------------
# 9. Start the unified FastAPI + Flet app
# ---------------------------------------------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
