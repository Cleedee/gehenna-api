FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///database.db
ENV SECRET_KEY=dev-secret-key-change-this

EXPOSE 8002 5000

CMD ["uv", "run", "task", "web"]