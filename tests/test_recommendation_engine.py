"""
Tests for Recommendation Engine Module
=====================================
"""

import pytest
from datetime import datetime
from modules.recommendation_engine import (
    RecommendationEngine,
    StockRecommendation,
    PriceLevels,
    StrategyMetrics,
    StrategyType,
    RiskLevel
)


class TestRecommendationEngine:
    """Test cases for RecommendationEngine class."""

    @pytest.fixture
    def engine(self):
        """Create a RecommendationEngine instance for testing."""
        return RecommendationEngine()

    def test_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert engine.default_risk_reward == 2.0
        assert engine.min_risk_reward == 1.5

    def test_calculate_price_levels(self, engine):
        """Test price level calculation."""
        levels = engine._calculate_price_levels(
            entry_price=10000,
            target_pct=10.0,
            stop_loss_pct=2.0
        )

        assert levels.entry_price == 10000
        assert levels.target_price == 11000
        assert levels.stop_loss_price == 9800
        assert levels.target_pct == 10.0
        assert levels.stop_loss_pct == 2.0
        assert levels.risk_reward_ratio == 5.0

    def test_determine_risk_level_low(self, engine):
        """Test risk level determination for low risk."""
        risk = engine._determine_risk_level(
            stop_loss_pct=1.5,
            volume_spike=2.5,
            spread=0.2
        )
        assert risk == RiskLevel.VERY_LOW

    def test_determine_risk_level_high(self, engine):
        """Test risk level determination for high risk."""
        risk = engine._determine_risk_level(
            stop_loss_pct=8.0,
            volume_spike=1.0,
            spread=1.0
        )
        assert risk in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]

    def test_calculate_confidence_score(self, engine):
        """Test confidence score calculation."""
        confidence = engine._calculate_confidence_score(
            score=85,
            volume_spike=2.5,
            spread=0.2,
            signal='STRONG BUY'
        )
        assert confidence > 50
        assert confidence <= 100

    def test_generate_rationale_buy(self, engine):
        """Test rationale generation for buy signal."""
        rationale = engine._generate_rationale(
            ticker="BBCA.JK",
            signal="BUY",
            score=80,
            price_change=3.5,
            volume_spike=2.5
        )
        assert "BBCA.JK" in rationale
        assert "BUY" in rationale or "buy" in rationale.lower()

    def test_determine_strategy_aggressive(self, engine):
        """Test strategy determination for aggressive."""
        strategy = engine._determine_strategy("STRONG BUY", 90, 5.0)
        assert strategy == StrategyType.AGGRESSIVE

    def test_determine_strategy_moderate(self, engine):
        """Test strategy determination for moderate."""
        strategy = engine._determine_strategy("BUY", 75, 2.0)
        assert strategy == StrategyType.MODERATE

    def test_determine_strategy_conservative(self, engine):
        """Test strategy determination for conservative."""
        strategy = engine._determine_strategy("HOLD", 60, 1.0)
        assert strategy == StrategyType.CONSERVATIVE

    def test_generate_recommendation(self, engine):
        """Test complete recommendation generation."""
        rec = engine.generate_recommendation(
            ticker="BBCA.JK",
            name="Bank Central Asia",
            price=10000,
            change_pct=2.5,
            volume_spike=2.5,
            spread=0.2,
            market_cap=100_000_000_000_000,
            score=85,
            signal="STRONG BUY"
        )

        assert isinstance(rec, StockRecommendation)
        assert rec.ticker == "BBCA.JK"
        assert rec.signal == "STRONG BUY"
        assert rec.price_levels is not None
        assert rec.metrics is not None
        assert rec.rationale is not None
        assert rec.key_levels is not None

    def test_generate_batch_recommendations(self, engine):
        """Test batch recommendation generation."""
        stocks = [
            {
                'ticker': 'BBCA.JK',
                'name': 'Bank Central Asia',
                'price': 10000,
                'change_pct': 2.5,
                'volume_spike': 2.5,
                'spread': 0.2,
                'market_cap': 100_000_000_000_000,
                'score': 85,
                'signal': 'STRONG BUY'
            },
            {
                'ticker': 'BBRI.JK',
                'name': 'Bank Rakyat Indonesia',
                'price': 5000,
                'change_pct': 1.0,
                'volume_spike': 1.5,
                'spread': 0.3,
                'market_cap': 80_000_000_000_000,
                'score': 75,
                'signal': 'BUY'
            }
        ]

        recs = engine.generate_batch_recommendations(stocks)
        assert len(recs) == 2
        assert all(isinstance(r, StockRecommendation) for r in recs)

    def test_get_strategy_summary(self, engine):
        """Test strategy summary retrieval."""
        summary = engine.get_strategy_summary(StrategyType.AGGRESSIVE)

        assert summary['type'] == 'AGGRESSIVE'
        assert 'target_profit' in summary
        assert 'max_loss' in summary
        assert 'holding_period' in summary
        assert 'position_size' in summary

    def test_compare_strategies(self, engine):
        """Test strategy comparison."""
        df = engine.compare_strategies("BBCA.JK", 10000)

        assert len(df) == len(StrategyType)
        assert 'Strategy' in df.columns
        assert 'Risk/Reward' in df.columns
        assert 'Target Profit' in df.columns

    def test_format_recommendation_text(self, engine):
        """Test recommendation text formatting."""
        rec = engine.generate_recommendation(
            ticker="BBCA.JK",
            name="Bank Central Asia",
            price=10000,
            change_pct=2.5,
            volume_spike=2.5,
            spread=0.2,
            market_cap=100_000_000_000_000,
            score=85,
            signal="STRONG BUY"
        )

        text = engine.format_recommendation_text(rec)
        assert "BBCA.JK" in text
        assert "STRONG BUY" in text
        assert "Entry" in text
        assert "Target" in text


class TestStrategyType:
    """Test cases for StrategyType enum."""

    def test_strategy_values(self):
        """Test all strategy type values exist."""
        assert StrategyType.AGGRESSIVE.value == "AGGRESSIVE"
        assert StrategyType.MODERATE.value == "MODERATE"
        assert StrategyType.CONSERVATIVE.value == "CONSERVATIVE"
        assert StrategyType.SWING.value == "SWING"
        assert StrategyType.INTRADAY.value == "INTRADAY"


class TestRiskLevel:
    """Test cases for RiskLevel enum."""

    def test_risk_level_values(self):
        """Test all risk level values exist."""
        assert RiskLevel.VERY_LOW.value == "VERY LOW"
        assert RiskLevel.LOW.value == "LOW"
        assert RiskLevel.MEDIUM.value == "MEDIUM"
        assert RiskLevel.HIGH.value == "HIGH"
        assert RiskLevel.VERY_HIGH.value == "VERY HIGH"


class TestPriceLevels:
    """Test cases for PriceLevels dataclass."""

    def test_price_levels_creation(self):
        """Test PriceLevels creation."""
        levels = PriceLevels(
            entry_price=10000,
            target_price=11000,
            stop_loss_price=9800,
            target_pct=10.0,
            stop_loss_pct=2.0,
            risk_reward_ratio=5.0
        )

        assert levels.entry_price == 10000
        assert levels.target_price == 11000
        assert levels.stop_loss_price == 9800
        assert levels.risk_reward_ratio == 5.0


class TestStrategyMetrics:
    """Test cases for StrategyMetrics dataclass."""

    def test_strategy_metrics_creation(self):
        """Test StrategyMetrics creation."""
        metrics = StrategyMetrics(
            strategy_type=StrategyType.AGGRESSIVE,
            risk_level=RiskLevel.MEDIUM,
            confidence_score=85.0,
            holding_period="1-3 days",
            max_loss_amount=200.0,
            max_profit_amount=1000.0,
            position_size_recommendation="5-10% of portfolio"
        )

        assert metrics.strategy_type == StrategyType.AGGRESSIVE
        assert metrics.risk_level == RiskLevel.MEDIUM
        assert metrics.confidence_score == 85.0
        assert metrics.holding_period == "1-3 days"
