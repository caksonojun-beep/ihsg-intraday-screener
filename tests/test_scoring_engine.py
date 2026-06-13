"""
Tests for Scoring Engine Module
================================
"""

import pytest
from datetime import datetime
from modules.scoring_engine import (
    ScoringEngine,
    ScoredStock,
    ScoreBreakdown,
    SignalType
)


class TestScoringEngine:
    """Test cases for ScoringEngine class."""

    @pytest.fixture
    def engine(self):
        """Create a ScoringEngine instance for testing."""
        return ScoringEngine()

    def test_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert engine.min_score == 50
        assert engine.max_score == 100
        assert 'volume_spike' in engine.weights
        assert 'bo_ratio' in engine.weights

    def test_custom_weights(self):
        """Test engine with custom weights."""
        custom_weights = {
            'volume_spike': 30.0,
            'bo_ratio': 30.0,
            'price_change': 20.0,
            'spread': 10.0,
            'market_cap': 10.0
        }
        engine = ScoringEngine(weights=custom_weights)
        assert engine.weights == custom_weights

    def test_calculate_volume_score_excellent(self, engine):
        """Test volume score for excellent volume spike."""
        score, factor = engine._calculate_volume_score(3.5)
        assert score == 100.0
        assert factor == "Exceptional volume surge"

    def test_calculate_volume_score_good(self, engine):
        """Test volume score for good volume spike."""
        score, factor = engine._calculate_volume_score(2.5)
        assert 75 <= score <= 100
        assert factor == "Strong volume activity"

    def test_calculate_volume_score_low(self, engine):
        """Test volume score for low volume."""
        score, factor = engine._calculate_volume_score(0.5)
        assert score < 25
        assert factor == "Low volume"

    def test_calculate_bo_ratio_score(self, engine):
        """Test BO ratio score calculation."""
        score, factor = engine._calculate_bo_ratio_score(1.5)
        assert score == 100.0
        assert factor == "Very high buy pressure"

    def test_calculate_price_change_score_optimal(self, engine):
        """Test price change score for optimal momentum."""
        score, factor = engine._calculate_price_change_score(3.0)
        assert score == 100.0
        assert factor == "Optimal momentum"

    def test_calculate_price_change_score_overbought(self, engine):
        """Test price change score for overbought."""
        score, factor = engine._calculate_price_change_score(8.0)
        assert score < 100
        assert factor == "Overbought territory"

    def test_calculate_spread_score(self, engine):
        """Test spread score calculation."""
        score, factor = engine._calculate_spread_score(0.05)
        assert score == 100.0
        assert factor == "Excellent liquidity"

    def test_calculate_market_cap_score_large(self, engine):
        """Test market cap score for large cap."""
        score, factor = engine._calculate_market_cap_score(150_000_000_000_000)
        assert score == 100.0
        assert factor == "Large cap blue chip"

    def test_calculate_market_cap_score_small(self, engine):
        """Test market cap score for small cap."""
        score, factor = engine._calculate_market_cap_score(500_000_000_000)
        assert 0 < score < 50
        assert factor == "Small cap stock"

    def test_determine_signal_strong_buy(self, engine):
        """Test signal determination for strong buy."""
        signal = engine._determine_signal(90)
        assert signal == SignalType.STRONG_BUY

    def test_determine_signal_buy(self, engine):
        """Test signal determination for buy."""
        signal = engine._determine_signal(75)
        assert signal == SignalType.BUY

    def test_determine_signal_hold(self, engine):
        """Test signal determination for hold."""
        signal = engine._determine_signal(60)
        assert signal == SignalType.HOLD

    def test_determine_signal_sell(self, engine):
        """Test signal determination for sell."""
        signal = engine._determine_signal(35)
        assert signal == SignalType.SELL

    def test_determine_signal_strong_sell(self, engine):
        """Test signal determination for strong sell."""
        signal = engine._determine_signal(20)
        assert signal == SignalType.STRONG_SELL

    def test_calculate_score_complete(self, engine):
        """Test complete score calculation."""
        scored = engine.calculate_score(
            ticker="BBCA.JK",
            name="Bank Central Asia",
            price=10000,
            change_pct=2.5,
            volume_spike=2.5,
            bo_ratio=1.3,
            spread=0.2,
            market_cap=100_000_000_000_000
        )

        assert isinstance(scored, ScoredStock)
        assert scored.ticker == "BBCA.JK"
        assert scored.score >= 50
        assert scored.signal in SignalType
        assert scored.score_breakdown is not None

    def test_score_batch(self, engine):
        """Test batch scoring."""
        stocks_data = [
            {
                'ticker': 'BBCA.JK',
                'name': 'Bank Central Asia',
                'price': 10000,
                'change_pct': 2.5,
                'volume_spike': 2.5,
                'bo_ratio': 1.3,
                'spread': 0.2,
                'market_cap': 100_000_000_000_000
            },
            {
                'ticker': 'BBRI.JK',
                'name': 'Bank Rakyat Indonesia',
                'price': 5000,
                'change_pct': 1.0,
                'volume_spike': 1.5,
                'bo_ratio': 1.0,
                'spread': 0.3,
                'market_cap': 80_000_000_000_000
            }
        ]

        scored = engine.score_batch(stocks_data)
        assert len(scored) == 2
        assert all(isinstance(s, ScoredStock) for s in scored)

    def test_filter_by_score(self, engine):
        """Test score filtering."""
        stocks = [
            ScoredStock(
                ticker="A", name="A", price=100, change_pct=1,
                volume_spike=1, bo_ratio=1, spread=0.1, market_cap=1e12,
                score=80, signal=SignalType.BUY,
                score_breakdown=ScoreBreakdown(0, 0, 0, 0, 0, 80, SignalType.BUY),
                last_updated=datetime.now()
            ),
            ScoredStock(
                ticker="B", name="B", price=100, change_pct=1,
                volume_spike=1, bo_ratio=1, spread=0.1, market_cap=1e12,
                score=40, signal=SignalType.SELL,
                score_breakdown=ScoreBreakdown(0, 0, 0, 0, 0, 40, SignalType.SELL),
                last_updated=datetime.now()
            )
        ]

        filtered = engine.filter_by_score(stocks, min_score=50)
        assert len(filtered) == 1
        assert filtered[0].ticker == "A"

    def test_sort_stocks(self, engine):
        """Test stock sorting."""
        stocks = [
            ScoredStock(
                ticker="A", name="A", price=100, change_pct=1,
                volume_spike=1, bo_ratio=1, spread=0.1, market_cap=1e12,
                score=40, signal=SignalType.SELL,
                score_breakdown=ScoreBreakdown(0, 0, 0, 0, 0, 40, SignalType.SELL),
                last_updated=datetime.now()
            ),
            ScoredStock(
                ticker="B", name="B", price=100, change_pct=3,
                volume_spike=2, bo_ratio=1.5, spread=0.1, market_cap=1e12,
                score=80, signal=SignalType.BUY,
                score_breakdown=ScoreBreakdown(0, 0, 0, 0, 0, 80, SignalType.BUY),
                last_updated=datetime.now()
            )
        ]

        sorted_stocks = engine.sort_stocks(stocks, by='score', ascending=False)
        assert sorted_stocks[0].score == 80
        assert sorted_stocks[1].score == 40

    def test_get_top_picks(self, engine):
        """Test getting top picks."""
        stocks = [
            ScoredStock(
                ticker="A", name="A", price=100, change_pct=1,
                volume_spike=1, bo_ratio=1, spread=0.1, market_cap=1e12,
                score=60, signal=SignalType.HOLD,
                score_breakdown=ScoreBreakdown(0, 0, 0, 0, 0, 60, SignalType.HOLD),
                last_updated=datetime.now()
            ),
            ScoredStock(
                ticker="B", name="B", price=100, change_pct=3,
                volume_spike=2, bo_ratio=1.5, spread=0.1, market_cap=1e12,
                score=90, signal=SignalType.STRONG_BUY,
                score_breakdown=ScoreBreakdown(0, 0, 0, 0, 0, 90, SignalType.STRONG_BUY),
                last_updated=datetime.now()
            ),
            ScoredStock(
                ticker="C", name="C", price=100, change_pct=2,
                volume_spike=1.5, bo_ratio=1.2, spread=0.1, market_cap=1e12,
                score=75, signal=SignalType.BUY,
                score_breakdown=ScoreBreakdown(0, 0, 0, 0, 0, 75, SignalType.BUY),
                last_updated=datetime.now()
            )
        ]

        top_picks = engine.get_top_picks(stocks, n=2)
        assert len(top_picks) == 2
        assert top_picks[0].score >= top_picks[1].score

    def test_to_dataframe(self, engine):
        """Test DataFrame conversion."""
        stocks = [
            ScoredStock(
                ticker="BBCA.JK", name="Bank Central Asia", price=10000,
                change_pct=2.5, volume_spike=2.5, bo_ratio=1.3, spread=0.2,
                market_cap=100_000_000_000_000, score=85,
                signal=SignalType.STRONG_BUY,
                score_breakdown=ScoreBreakdown(100, 100, 100, 100, 100, 85, SignalType.STRONG_BUY),
                last_updated=datetime.now()
            )
        ]

        df = engine.to_dataframe(stocks)
        assert len(df) == 1
        assert 'Ticker' in df.columns
        assert 'Score' in df.columns
        assert 'Signal' in df.columns


class TestSignalType:
    """Test cases for SignalType enum."""

    def test_signal_values(self):
        """Test all signal type values exist."""
        assert SignalType.STRONG_BUY.value == "STRONG BUY"
        assert SignalType.BUY.value == "BUY"
        assert SignalType.HOLD.value == "HOLD"
        assert SignalType.SELL.value == "SELL"
        assert SignalType.STRONG_SELL.value == "STRONG SELL"


class TestScoreBreakdown:
    """Test cases for ScoreBreakdown dataclass."""

    def test_score_breakdown_creation(self):
        """Test ScoreBreakdown creation."""
        breakdown = ScoreBreakdown(
            volume_score=80.0,
            bo_ratio_score=75.0,
            price_change_score=90.0,
            spread_score=85.0,
            market_cap_score=95.0,
            total_score=85,
            signal=SignalType.BUY,
            score_factors={'volume': 'Strong volume activity'}
        )

        assert breakdown.volume_score == 80.0
        assert breakdown.total_score == 85
        assert breakdown.signal == SignalType.BUY
