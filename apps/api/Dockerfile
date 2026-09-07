FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir .
EXPOSE 8000
CMD ["sh", "-c", "uvicorn signalroom.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
