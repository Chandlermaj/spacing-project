# 1. Use a lightweight Python image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the dependency list
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your code into the container
COPY . .

# 6. Expose the port FastAPI will use
EXPOSE 8000

# --- Force inject Railway environment variables ---
ENV SUPABASE_URL=${SUPABASE_URL}
ENV SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
ENV MAPBOX_TOKEN=${MAPBOX_TOKEN}
ENV API_URL=${API_URL}

# 7. Start the FastAPI app
CMD ["python", "main.py"]
