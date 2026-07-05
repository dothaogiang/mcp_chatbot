FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-vie \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY mcp/requirements.txt ./mcp-requirements.txt
COPY rag/requirements.txt ./rag-requirements.txt
RUN pip install --no-cache-dir -r mcp-requirements.txt -r rag-requirements.txt

COPY mcp/ ./mcp/
COPY rag/ ./rag/

ENV PYTHONPATH=/app:/app/mcp/src

CMD ["python", "mcp/src/server.py"]