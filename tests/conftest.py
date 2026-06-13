"""
Pytest Configuration
=====================
"""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def project_root():
    """Get project root directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """Get test data directory."""
    return os.path.join(project_root, "tests", "data")


@pytest.fixture
def sample_tickers():
    """Provide sample tickers for testing."""
    return ["BBCA.JK", "BBRI.JK", "BMRI.JK"]


@pytest.fixture
def sample_stock_data():
    """Provide sample stock data for testing."""
    return {
        'ticker': 'BBCA.JK',
        'name': 'Bank Central Asia',
        'price': 10000,
        'change_pct': 2.5,
        'volume_spike': 2.5,
        'bo_ratio': 1.3,
        'spread': 0.2,
        'market_cap': 100_000_000_000_000
    }


@pytest.fixture
def sample_candle_data():
    """Provide sample candlestick data for testing."""
    from datetime import datetime, timedelta

    timestamps = [datetime.now() + timedelta(hours=i) for i in range(10)]
    return {
        'timestamps': timestamps,
        'opens': [100 + i for i in range(10)],
        'highs': [105 + i for i in range(10)],
        'lows': [95 + i for i in range(10)],
        'closes': [102 + i for i in range(10)],
        'volumes': [1000000 + i * 10000 for i in range(10)]
    }
