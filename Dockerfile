FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml requirements.txt Readme.md ./
COPY payout_engine ./payout_engine
COPY api ./api
COPY cli ./cli
COPY web ./web

RUN pip install --no-cache-dir -e .

EXPOSE 8000

# Railway injects PORT; bind explicitly via shell so it expands.
CMD ["sh", "-c", "exec uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
