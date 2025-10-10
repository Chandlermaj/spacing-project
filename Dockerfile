# ===============================================================
# 1. Base image
# ===============================================================
FROM python:3.11-slim

# ---------------------------------------------------------------
# 2. Install Chrome + fonts + supervisor
# ---------------------------------------------------------------
RUN apt-get update && \
    apt-get install -y wget gnupg ca-certificates fonts-liberation libnss3 supervisor && \
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
# 4. Python dependencies
# ---------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------
# 5. Copy project
# ---------------------------------------------------------------
COPY . .

# ---------------------------------------------------------------
# 6. Supervisor config
# ---------------------------------------------------------------
RUN mkdir -p /etc/supervisor/conf.d
COPY <<EOF /etc/supervisor/conf.d/spacing.conf
[supervisord]
nodaemon=true

[program:fastapi]
command=uvicorn main:app --host 0.0.0.0 --port 8000
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stderr_logfile=/dev/stderr

[program:flet]
command=python main.py
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stderr_logfile=/dev/stderr
EOF

# ---------------------------------------------------------------
# 7. Ports
# ---------------------------------------------------------------
EXPOSE 8000
EXPOSE 8550

# ---------------------------------------------------------------
# 8. Environment
# ---------------------------------------------------------------
ENV PYTHONUNBUFFERED=1 \
    PATH="/usr/bin/google-chrome:$PATH" \
    SUPABASE_URL=${SUPABASE_URL} \
    SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY} \
    MAPBOX_TOKEN=${MAPBOX_TOKEN} \
    API_URL=${API_URL}

# ---------------------------------------------------------------
# 9. Verify Chrome (optional)
# ---------------------------------------------------------------
RUN google-chrome --version || echo "⚠️ Chrome not found!"

# ---------------------------------------------------------------
# 10. Start both FastAPI and Flet
# ---------------------------------------------------------------
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/spacing.conf"]
