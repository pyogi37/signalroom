FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir .

# The seed replays recorded model runs, so the image needs the fixtures and the
# recordings. Both are synthetic and carry no key.
COPY evals ./evals
COPY recordings ./recordings
ENV SIGNALROOM_FIXTURES_DIR=/app/evals/fixtures \
    SIGNALROOM_RECORDINGS_DIR=/app/recordings \
    SIGNALROOM_EVAL_RESULTS=/app/evals/results/latest.json \
    SIGNALROOM_MODEL_MODE=replay \
    SIGNALROOM_DATA_DIR=/app/data

EXPOSE 8000
# Hosts that inject their own PORT are respected; 8000 locally.
CMD ["sh", "-c", "uvicorn signalroom.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
