# ===============================================================
# Base image
# ===============================================================
FROM python:3.11-slim

# ---------------------------------------------------------------
# Install Chrome + fonts for Plotly/Kaleido
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
# Working directory
# ---------------------------------------------------------------
WORKDIR /app

# ---------------------------------------------------------------
# Install dependencies
# ---------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install flet==0.28.3 flet-web==0.28.3

# ---------------------------------------------------------------
# Copy project files
# ---------------------------------------------------------------
COPY . .

# ---------------------------------------------------------------
# Expose both ports (FastAPI + Flet)
# ---------------------------------------------------------------
EXPOSE 8000
EXPOSE 8550

# ---------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------
ENV PYTHONUNBUFFERED=1 \
    PATH="/usr/bin/google-chrome:$PATH"

# ---------------------------------------------------------------
# Run both apps (Flet UI will be main entrypoint)
# ---------------------------------------------------------------
CMD ["python", "main.py"]
