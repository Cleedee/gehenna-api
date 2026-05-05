FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    "pydantic[email]" \
    pydantic-settings \
    sqlalchemy \
    alembic \
    python-jose \
    "passlib[bcrypt]" \
    python-multipart \
    tinydb \
    requests \
    pyjsonq \
    httpx \
    flask \
    flask-wtf \
    wtforms

COPY . .

ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///database.db
ENV SECRET_KEY=dev-secret-key-change-this

EXPOSE 8002 5000

CMD ["python", "-m", "uvicorn", "gehenna_api.app:app", "--host", "0.0.0.0", "--port", "8002"] & \
    ["python", "gehenna_web/run.py"]