FROM python:3.12-slim
WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip uv

# copy trước để cache layer, chỉ rebuild dependency khi pyproject/uv.lock đổi
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . /app

EXPOSE 8000
CMD ["uv", "run", "python", "src/server.py"]