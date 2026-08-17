FROM python:3.12-slim

WORKDIR /workspace
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .
COPY . .
