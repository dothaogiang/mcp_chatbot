FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-vie \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .env.example .env

WORKDIR /app/src
EXPOSE 8091

# CMD mặc định chạy API; service ingestion trong docker-compose sẽ override
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8091"]
