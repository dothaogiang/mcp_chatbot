FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY Resources/ ./Resources/
COPY .env.example .env

WORKDIR /app/src
EXPOSE 8090
CMD ["python", "server.py"]
