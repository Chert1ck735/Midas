FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    DATA_DIR=/data \
    DRY_RUN=true \
    PAPER_TRADING=false \
    MARKET_DATA_PROVIDER=iss \
    LLM_ENABLED=false

WORKDIR /app

# LightGBM requires the OpenMP runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY data/models ./data/models
COPY LICENSE ./

# Supply credentials at runtime with --env-file or -e.
RUN mkdir -p /data

CMD ["python", "-m", "moex_agent"]
