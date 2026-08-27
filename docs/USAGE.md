# Operator UI

```bash
pip install -e ".[dev]"
uvicorn api.app:app --reload --port 8000
```

Open `http://127.0.0.1:8000/` for the Kanggiten Prize Engine console.

Generate uses **Slot / casino** vs **Ticketed** recipes. Advanced options are collapsed by default. Suggestions appear when a setup looks weak or a generate fails.

Deploy (Railway): `Procfile` + `railway.json` start `uvicorn api.app:app` with `/health` check.

`POST /v1/payouts/generate|analyze|optimize|recalibrate`
