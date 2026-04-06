FROM python:3.11-slim
WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md ./
RUN pip install --upgrade pip && pip install -e .[dev]
COPY . .
RUN chmod +x /workspace/scripts/docker-entrypoint.sh

EXPOSE 8000
CMD ["/workspace/scripts/docker-entrypoint.sh"]
