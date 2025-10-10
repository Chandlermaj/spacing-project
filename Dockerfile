# ===============================================================
# 1. Base image
# ===============================================================
FROM python:3.11-slim

# ---------------------------------------------------------------
# 2. Install Google Chrome and required system libs
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
# 4. Install Python dependencies (Flet 0.28.3 + flet-web 0.28.3)
# ---------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install flet==0.28.3 flet-web==0.28.3

# ---------------------------------------------------------------
# 5. Copy project code
# ---------------------------------------------------------------
COPY . .

# ---------------------------------------------------------------
# 6. Expose both ports
# ---------------------------------------------------------------
EXPOSE 8000     # FastAPI backend
EXPOSE 8550     # Flet web UI

# ---------------------------------------------------------------
# 7. Environment variables
# ---------------------------------------------------------------
ENV PYTHONUNBUFFERED=1 \
    PATH="/usr/bin/google-chrome:$PATH" \
    SUPABASE_URL=${SUPABASE_URL} \
    SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY} \
    MAPBOX_TOKEN=${MAPBOX_TOKEN} \
    API_URL=${API_URL}

# ---------------------------------------------------------------
# 8. Verify Chrome (optional)
# ---------------------------------------------------------------
RUN google-chrome --version || echo "⚠️ Chrome not found!"

# ---------------------------------------------------------------
# 9. Run FastAPI (port 8000) + Flet Web UI (port 8550)
# ---------------------------------------------------------------
CMD ["python", "main.py"]
