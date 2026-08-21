# FastAPI backend + the Node/TS Baileys bridge it spawns as a subprocess (see
# app/core/bridge_process.py). Both runtimes live in one image because the API process manages
# the bridge's lifecycle directly, same as the reference repo this project extends.
FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]" || pip install --no-cache-dir -e .

COPY whatsapp_bridge/package.json whatsapp_bridge/package-lock.json* whatsapp_bridge/
RUN cd whatsapp_bridge && npm install

COPY app ./app
COPY whatsapp_bridge ./whatsapp_bridge
COPY scripts ./scripts

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
