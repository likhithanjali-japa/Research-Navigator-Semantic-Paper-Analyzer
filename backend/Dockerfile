FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install only backend deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend source
COPY backend /app/backend

ENV MONGO_URL=mongodb://mongo:27017/paperiq \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
