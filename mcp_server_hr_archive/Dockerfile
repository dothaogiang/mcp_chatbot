FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --upgrade pip && pip install uv
RUN uv install --no-interaction
COPY . /app
EXPOSE 8000
CMD ["uv", "run", "python", "src/server.py"]
