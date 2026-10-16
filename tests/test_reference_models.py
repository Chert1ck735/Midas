"""The distributed artifacts must load with the project's pinned dependencies."""
from datetime import datetime, timezone
from pathlib import Path
import warnings

import pytest
from sklearn.exceptions import InconsistentVersionWarning

from moex_agent.ml_filter import MLBuyFilter
from moex_agent.models import MarketFeatures


@pytest.mark.parametrize(('name', 'label'), [
    ('lgbm_buy_filter_v5', 'up'),
    ('lgbm_short_filter_v2', 'down'),
])
def test_reference_model_loads_and_predicts_without_version_mismatch(name, label):
    model_path = Path(__file__).resolve().parents[1] / 'data' / 'models' / f'{name}.joblib'
    with warnings.catch_warnings():
        warnings.simplefilter('error', InconsistentVersionWarning)
        model = MLBuyFilter.load(model_path, positive_label=label)
    assert model is not None, 'Distributed model must load without sklearn version mismatch'
    features = MarketFeatures(
        symbol='SBER', feature_ts=datetime(2026, 10, 16, 12, tzinfo=timezone.utc),
        price=300.0, rsi=35.0, macd=0.1, macd_signal=0.0,
        bollinger_low=299.0, bollinger_mid=303.0, bollinger_high=307.0,
        atr_pct=0.01, volume_ratio=1.0,
    )
    assert 0.0 <= model.predict_up_probability(features) <= 1.0
