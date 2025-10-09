# ===============================================================
# 1. Base image — lightweight Python image
# ===============================================================
FROM python:3.11-slim

# ---------------------------------------------------------------
# 2. Install system dependencies (Google Chrome + fonts)
# ---------------------------------------------------------------
RUN apt-get update && \
    apt-get install -y wget gnupg ca-certificates fonts-liberation libnss3 && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------
# 3. Set the working directory
# ---------------------------------------------------------------
WORKDIR /app

# ---------------------------------------------------------------
# 4. Copy dependency list and install Python packages
# ---------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------
# 5. Copy your project code
# ---------------------------------------------------------------
COPY . .

# ---------------------------------------------------------------
# 6. Expose FastAPI port
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
# 8. Verify Chrome installation (optional debug)
# ---------------------------------------------------------------
RUN google-chrome --version || echo "⚠️ Chrome not found!"

# ---------------------------------------------------------------
# 9. Start FastAPI + Flet app
# ---------------------------------------------------------------
CMD ["python", "main.py"]
