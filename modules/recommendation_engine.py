"""
IHSG Stock Screener - Recommendation Engine Module
=====================================================
Generates trading recommendations including entry, target, and stop loss.
Provides strategy cards with risk-reward analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np


class StrategyType(Enum):
    """Enumeration of trading strategy types."""
    AGGRESSIVE = "AGGRESSIVE"
    MODERATE = "MODERATE"
    CONSERVATIVE = "CONSERVATIVE"
    SWING = "SWING"
    INTRADAY = "INTRADAY"


class RiskLevel(Enum):
    """Enumeration of risk levels."""
    VERY_LOW = "VERY LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY HIGH"


@dataclass
class PriceLevels:
    """Trading price levels (entry, target, stop loss)."""
    entry_price: float
    target_price: float
    stop_loss_price: float
    target_pct: float
    stop_loss_pct: float
    risk_reward_ratio: float


@dataclass
class StrategyMetrics:
    """Detailed strategy metrics and analysis."""
    strategy_type: StrategyType
    risk_level: RiskLevel
    confidence_score: float
    holding_period: str
    max_loss_amount: float
    max_profit_amount: float
    position_size_recommendation: str


@dataclass
class StockRecommendation:
    """Complete trading recommendation for a stock."""
    ticker: str
    name: str
    signal: str
    strategy: StrategyType
    price_levels: PriceLevels
    metrics: StrategyMetrics
    rationale: str
    key_levels: Dict[str, float]
    indicators: Dict[str, any]
    generated_at: datetime


class RecommendationEngine:
    """
    Recommendation Engine for generating trading recommendations.

    Features:
    - Multiple strategy types (Aggressive, Moderate, Conservative)
    - Dynamic price level calculation
    - Risk-reward analysis
    - Position sizing recommendations
    - Confidence scoring
    """

    def __init__(
        self,
        default_risk_reward: float = 2.0,
        min_risk_reward: float = 1.5
    ):
        """
        Initialize the Recommendation Engine.

        Args:
            default_risk_reward: Default risk-reward ratio
            min_risk_reward: Minimum acceptable risk-reward ratio
        """
        self.default_risk_reward = default_risk_reward
        self.min_risk_reward = min_risk_reward

        # Strategy configurations
        self.strategy_configs = {
            StrategyType.AGGRESSIVE: {
                'target_pct': 10.0,
                'stop_loss_pct': 2.0,
                'holding_period': '1-3 days',
                'position_size': '5-10% of portfolio'
            },
            StrategyType.MODERATE: {
                'target_pct': 5.0,
                'stop_loss_pct': 3.0,
                'holding_period': '1-2 weeks',
                'position_size': '10-15% of portfolio'
            },
            StrategyType.CONSERVATIVE: {
                'target_pct': 3.0,
                'stop_loss_pct': 2.0,
                'holding_period': '2-4 weeks',
                'position_size': '15-20% of portfolio'
            },
            StrategyType.SWING: {
                'target_pct': 8.0,
                'stop_loss_pct': 4.0,
                'holding_period': '1-4 weeks',
                'position_size': '10-15% of portfolio'
            },
            StrategyType.INTRADAY: {
                'target_pct': 2.0,
                'stop_loss_pct': 1.0,
                'holding_period': 'Same day',
                'position_size': '3-5% of portfolio'
            }
        }

        # Risk level thresholds
        self.risk_thresholds = {
            RiskLevel.VERY_LOW: (0, 1.0),
            RiskLevel.LOW: (1.0, 2.0),
            RiskLevel.MEDIUM: (2.0, 4.0),
            RiskLevel.HIGH: (4.0, 6.0),
            RiskLevel.VERY_HIGH: (6.0, float('inf'))
        }

    def _calculate_price_levels(
        self,
        entry_price: float,
        target_pct: float,
        stop_loss_pct: float
    ) -> PriceLevels:
        """
        Calculate trading price levels.

        Args:
            entry_price: Entry price for the trade
            target_pct: Target profit percentage
            stop_loss_pct: Stop loss percentage

        Returns:
            PriceLevels object with all price levels
        """
        target_price = entry_price * (1 + target_pct / 100)
        stop_loss_price = entry_price * (1 - stop_loss_pct / 100)

        risk_reward = target_pct / stop_loss_pct if stop_loss_pct > 0 else 0

        return PriceLevels(
            entry_price=entry_price,
            target_price=target_price,
            stop_loss_price=stop_loss_price,
            target_pct=target_pct,
            stop_loss_pct=stop_loss_pct,
            risk_reward_ratio=risk_reward
        )

    def _determine_risk_level(
        self,
        stop_loss_pct: float,
        volume_spike: float,
        spread: float
    ) -> RiskLevel:
        """
        Determine risk level based on multiple factors.

        Args:
            stop_loss_pct: Stop loss percentage
            volume_spike: Volume spike ratio
            spread: Bid-ask spread percentage

        Returns:
            RiskLevel enum value
        """
        # Calculate combined risk score
        risk_score = stop_loss_pct

        # Higher volume spike reduces risk
        if volume_spike >= 2.0:
            risk_score *= 0.8
        elif volume_spike >= 1.5:
            risk_score *= 0.9

        # Higher spread increases risk
        if spread > 0.5:
            risk_score *= 1.2
        elif spread > 0.3:
            risk_score *= 1.1

        # Determine risk level
        for level, (low, high) in self.risk_thresholds.items():
            if low <= risk_score < high:
                return level

        return RiskLevel.MEDIUM

    def _calculate_confidence_score(
        self,
        score: int,
        volume_spike: float,
        spread: float,
        signal: str
    ) -> float:
        """
        Calculate confidence score for the recommendation.

        Args:
            score: Stock score (0-100)
            volume_spike: Volume spike ratio
            spread: Bid-ask spread percentage
            signal: Trading signal

        Returns:
            Confidence score (0-100)
        """
        confidence = score * 0.4  # Base from stock score

        # Volume spike contribution
        if volume_spike >= 2.0:
            confidence += 20
        elif volume_spike >= 1.5:
            confidence += 10

        # Spread contribution
        if spread <= 0.3:
            confidence += 15
        elif spread <= 0.5:
            confidence += 10

        # Signal contribution
        if signal in ['STRONG BUY', 'BUY']:
            confidence += 15
        elif signal == 'HOLD':
            confidence += 5

        return min(100, max(0, confidence))

    def _generate_rationale(
        self,
        ticker: str,
        signal: str,
        score: int,
        price_change: float,
        volume_spike: float
    ) -> str:
        """
        Generate trading rationale text.

        Args:
            ticker: Stock ticker
            signal: Trading signal
            score: Stock score
            price_change: Price change percentage
            volume_spike: Volume spike ratio

        Returns:
            Rationale text
        """
        rationale_parts = []

        # Signal-based rationale
        if signal == 'STRONG BUY':
            rationale_parts.append(
                f"{ticker} shows strong buying momentum with a score of {score}."
            )
        elif signal == 'BUY':
            rationale_parts.append(
                f"{ticker} presents a buy opportunity with a score of {score}."
            )
        elif signal == 'HOLD':
            rationale_parts.append(
                f"{ticker} is recommended for holding with a score of {score}."
            )
        else:
            rationale_parts.append(
                f"{ticker} has a score of {score}."
            )

        # Price movement rationale
        if price_change > 3:
            rationale_parts.append(
                f"Strong upward momentum of {price_change:.1f}% suggests continued bullishness."
            )
        elif price_change > 1:
            rationale_parts.append(
                f"Moderate gain of {price_change:.1f}% indicates steady price action."
            )
        elif price_change > 0:
            rationale_parts.append(
                f"Slight positive movement of {price_change:.1f}%."
            )
        elif price_change < -3:
            rationale_parts.append(
                f"Significant decline of {price_change:.1f}% may indicate oversold conditions."
            )
        else:
            rationale_parts.append(
                f"Price movement of {price_change:.1f}%."
            )

        # Volume rationale
        if volume_spike >= 2.0:
            rationale_parts.append(
                f"Volume spike of {volume_spike:.1f}x average confirms institutional interest."
            )
        elif volume_spike >= 1.5:
            rationale_parts.append(
                f"Elevated volume of {volume_spike:.1f}x average shows increased activity."
            )

        return " ".join(rationale_parts)

    def _determine_strategy(
        self,
        signal: str,
        score: int,
        price_change: float
    ) -> StrategyType:
        """
        Determine appropriate trading strategy.

        Args:
            signal: Trading signal
            score: Stock score
            price_change: Price change percentage

        Returns:
            StrategyType enum value
        """
        if signal == 'STRONG BUY' and score >= 85:
            return StrategyType.AGGRESSIVE
        elif signal == 'BUY' and score >= 70:
            return StrategyType.MODERATE
        elif signal == 'HOLD':
            return StrategyType.CONSERVATIVE
        elif abs(price_change) > 5:
            return StrategyType.SWING
        else:
            return StrategyType.MODERATE

    def generate_recommendation(
        self,
        ticker: str,
        name: str,
        price: float,
        change_pct: float,
        volume_spike: float,
        spread: float,
        market_cap: float,
        score: int,
        signal: str
    ) -> StockRecommendation:
        """
        Generate complete trading recommendation.

        Args:
            ticker: Stock ticker symbol
            name: Company name
            price: Current price
            change_pct: Price change percentage
            volume_spike: Volume spike ratio
            spread: Bid-ask spread percentage
            market_cap: Market capitalization
            score: Stock score
            signal: Trading signal

        Returns:
            StockRecommendation object
        """
        # Determine strategy
        strategy = self._determine_strategy(signal, score, change_pct)
        config = self.strategy_configs[strategy]

        # Calculate price levels
        price_levels = self._calculate_price_levels(
            entry_price=price,
            target_pct=config['target_pct'],
            stop_loss_pct=config['stop_loss_pct']
        )

        # Determine risk level
        risk_level = self._determine_risk_level(
            stop_loss_pct=config['stop_loss_pct'],
            volume_spike=volume_spike,
            spread=spread
        )

        # Calculate confidence score
        confidence = self._calculate_confidence_score(
            score=score,
            volume_spike=volume_spike,
            spread=spread,
            signal=signal
        )

        # Calculate strategy metrics
        metrics = StrategyMetrics(
            strategy_type=strategy,
            risk_level=risk_level,
            confidence_score=confidence,
            holding_period=config['holding_period'],
            max_loss_amount=price * (config['stop_loss_pct'] / 100),
            max_profit_amount=price * (config['target_pct'] / 100),
            position_size_recommendation=config['position_size']
        )

        # Generate rationale
        rationale = self._generate_rationale(
            ticker=ticker,
            signal=signal,
            score=score,
            price_change=change_pct,
            volume_spike=volume_spike
        )

        # Key levels
        key_levels = {
            'entry': price,
            'target': price_levels.target_price,
            'stop_loss': price_levels.stop_loss_price,
            'resistance': price * 1.05,
            'support': price * 0.98
        }

        # Indicators
        indicators = {
            'volume_spike': volume_spike,
            'spread': spread,
            'market_cap': market_cap,
            'risk_reward': price_levels.risk_reward_ratio
        }

        return StockRecommendation(
            ticker=ticker,
            name=name,
            signal=signal,
            strategy=strategy,
            price_levels=price_levels,
            metrics=metrics,
            rationale=rationale,
            key_levels=key_levels,
            indicators=indicators,
            generated_at=datetime.now()
        )

    def generate_batch_recommendations(
        self,
        stocks: List[Dict]
    ) -> List[StockRecommendation]:
        """
        Generate recommendations for multiple stocks.

        Args:
            stocks: List of stock data dictionaries

        Returns:
            List of StockRecommendation objects
        """
        recommendations = []

        for stock in stocks:
            try:
                rec = self.generate_recommendation(
                    ticker=stock.get('ticker', ''),
                    name=stock.get('name', stock.get('ticker', '')),
                    price=stock.get('price', 0),
                    change_pct=stock.get('change_pct', 0),
                    volume_spike=stock.get('volume_spike', 0),
                    spread=stock.get('spread', 0),
                    market_cap=stock.get('market_cap', 0),
                    score=stock.get('score', 0),
                    signal=stock.get('signal', 'HOLD')
                )
                recommendations.append(rec)
            except Exception:
                continue

        return recommendations

    def get_strategy_summary(self, strategy: StrategyType) -> Dict:
        """
        Get summary of a strategy type.

        Args:
            strategy: StrategyType enum value

        Returns:
            Dictionary with strategy details
        """
        config = self.strategy_configs[strategy]

        return {
            'type': strategy.value,
            'target_profit': f"{config['target_pct']}%",
            'max_loss': f"{config['stop_loss_pct']}%",
            'holding_period': config['holding_period'],
            'position_size': config['position_size']
        }

    def compare_strategies(self, ticker: str, price: float) -> pd.DataFrame:
        """
        Compare all strategy types for a given ticker.

        Args:
            ticker: Stock ticker symbol
            price: Current price

        Returns:
            DataFrame comparing all strategies
        """
        comparisons = []

        for strategy_type in StrategyType:
            config = self.strategy_configs[strategy_type]
            levels = self._calculate_price_levels(
                entry_price=price,
                target_pct=config['target_pct'],
                stop_loss_pct=config['stop_loss_pct']
            )

            comparisons.append({
                'Strategy': strategy_type.value,
                'Target Profit': f"{config['target_pct']}%",
                'Stop Loss': f"{config['stop_loss_pct']}%",
                'Risk/Reward': f"{levels.risk_reward_ratio:.2f}",
                'Holding Period': config['holding_period'],
                'Position Size': config['position_size'],
                'Target Price': f"IDR {levels.target_price:,.0f}",
                'Stop Price': f"IDR {levels.stop_loss_price:,.0f}"
            })

        return pd.DataFrame(comparisons)

    def format_recommendation_text(self, rec: StockRecommendation) -> str:
        """
        Format recommendation as readable text.

        Args:
            rec: StockRecommendation object

        Returns:
            Formatted text string
        """
        lines = [
            f"📊 {rec.ticker} - {rec.name}",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Signal: {rec.signal}",
            f"Strategy: {rec.strategy.value}",
            f"",
            f"💰 Entry: IDR {rec.price_levels.entry_price:,.0f}",
            f"🎯 Target: IDR {rec.price_levels.target_price:,.0f} (+{rec.price_levels.target_pct}%)",
            f"🛡️ Stop Loss: IDR {rec.price_levels.stop_loss_price:,.0f} (-{rec.price_levels.stop_loss_pct}%)",
            f"📈 Risk/Reward: {rec.price_levels.risk_reward_ratio:.2f}",
            f"",
            f"⚠️ Risk Level: {rec.metrics.risk_level.value}",
            f"📊 Confidence: {rec.metrics.confidence_score:.0f}%",
            f"⏱️ Holding: {rec.metrics.holding_period}",
            f"💼 Position: {rec.metrics.position_size_recommendation}",
            f"",
            f"💡 {rec.rationale}"
        ]

        return "\n".join(lines)


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'RecommendationEngine',
    'StockRecommendation',
    'PriceLevels',
    'StrategyMetrics',
    'StrategyType',
    'RiskLevel'
]
