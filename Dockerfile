FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml requirements.txt Readme.md ./
COPY payout_engine ./payout_engine
COPY api ./api
COPY cli ./cli
COPY web ./web

RUN pip install --no-cache-dir -e .

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn api.app:app --host 0.0.0.0 --port ${PORT}"]
