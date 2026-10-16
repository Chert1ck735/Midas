"""Entry freshness accepts UTC-aware candles and naive Moscow API timestamps."""
from dataclasses import replace
from datetime import datetime, timezone
import json

import pytest

from moex_agent import app
from moex_agent.arena_client import ArenaClient
from moex_agent.market_data import SampleMarketDataClient
from moex_agent.memory import DecisionMemory
from moex_agent.models import MarketFeatures
from moex_agent.storage import JsonStore


@pytest.mark.parametrize(('timestamp', 'expected_action'), [
    ('2026-10-16T11:55:00+00:00', 'buy'),
    ('2026-10-16T14:55:00+03:00', 'buy'),
    ('2026-10-16T14:55:00', 'buy'),
    ('2026-10-16T11:00:00+00:00', 'hold'),
    ('2026-10-16T14:00:00', 'hold'),
])
def test_entry_freshness_normalizes_candle_timezone(monkeypatch, tmp_path, timestamp, expected_action):
    now = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)
    features = MarketFeatures(
        symbol='ALRS', feature_ts=datetime.fromisoformat(timestamp), price=100.0,
        rsi=30.0, macd=0.0, macd_signal=0.0,
        bollinger_low=100.0, bollinger_mid=102.0, bollinger_high=104.0,
        atr_pct=0.01, volume_ratio=1.0,
    )
    # Supply controlled market features; run the real strategy, risk layer and dry-run adapter.
    monkeypatch.setattr(app, 'build_features', lambda *args: features)
    monkeypatch.setattr(app, 'WATCHLIST', ['ALRS'])
    monkeypatch.setattr(app, 'utc_now', lambda: now)
    monkeypatch.setattr(app, 'settings', replace(
        app.settings, ml_filter_enabled=False, enable_shorts=False,
    ))
    store = JsonStore(tmp_path)
    client = ArenaClient('https://arenago.ru', '', bot_name='test', dry_run=True, paper_trading=False)
    app.run_once(client, SampleMarketDataClient(), app.build_risk_manager(), store, DecisionMemory(store))
    decision = json.loads((tmp_path / 'logs' / 'decisions.jsonl').read_text().splitlines()[0])
    assert decision['signal']['action'] == expected_action
    if expected_action == 'hold':
        assert 'stale data' in decision['signal']['reason']
    summary = json.loads((tmp_path / 'logs' / 'cycle_summary.jsonl').read_text())
    assert summary['decisions'] == 1
