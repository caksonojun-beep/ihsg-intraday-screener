"""
IHSG Stock Screener - Scoring Engine Module
===========================================
Calculates comprehensive stock scores based on multiple factors.
Generates trading signals based on score thresholds.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np


class SignalType(Enum):
    """Enumeration of trading signal types."""
    STRONG_BUY = "STRONG BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG SELL"


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of stock score components."""
    volume_score: float
    bo_ratio_score: float
    price_change_score: float
    spread_score: float
    market_cap_score: float
    total_score: int
    signal: SignalType
    score_factors: Dict[str, str] = field(default_factory=dict)


@dataclass
class ScoredStock:
    """Stock data with calculated score and signal."""
    ticker: str
    name: str
    price: float
    change_pct: float
    volume_spike: float
    bo_ratio: float
    spread: float
    market_cap: float
    score: int
    signal: SignalType
    score_breakdown: ScoreBreakdown
    last_updated: datetime


class ScoringEngine:
    """
    Scoring Engine for calculating comprehensive stock scores.

    Score Components:
    1. Volume Spike (25%): Volume relative to average volume
    2. Buy/Order Ratio (25%): Market activity indicator
    3. Price Change (20%): Recent price movement
    4. Spread (15%): Bid-ask spread tightness
    5. Market Cap (15%): Company size factor

    Total Score: 0-100
    Signals:
    - STRONG BUY: Score >= 85
    - BUY: Score >= 70
    - HOLD: Score >= 50
    - SELL: Score >= 30
    - STRONG SELL: Score < 30
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        min_score: int = 50,
        max_score: int = 100
    ):
        """
        Initialize the Scoring Engine.

        Args:
            weights: Custom weight dictionary for score components
            min_score: Minimum possible score
            max_score: Maximum possible score
        """
        self.default_weights = {
            'volume_spike': 25.0,
            'bo_ratio': 25.0,
            'price_change': 20.0,
            'spread': 15.0,
            'market_cap': 15.0
        }

        self.weights = weights if weights else self.default_weights
        self.min_score = min_score
        self.max_score = max_score

        # Score thresholds
        self.signal_thresholds = {
            SignalType.STRONG_BUY: 85,
            SignalType.BUY: 70,
            SignalType.HOLD: 50,
            SignalType.SELL: 30,
            SignalType.STRONG_SELL: 0
        }

        # Volume spike thresholds
        self.volume_thresholds = {
            'excellent': 3.0,  # 3x average
            'good': 2.0,       # 2x average
            'fair': 1.5,       # 1.5x average
            'poor': 1.0        # At or below average
        }

        # BO ratio thresholds
        self.bo_ratio_thresholds = {
            'excellent': 1.5,
            'good': 1.2,
            'fair': 1.0,
            'poor': 0.8
        }

        # Spread thresholds (as percentage)
        self.spread_thresholds = {
            'excellent': 0.1,  # < 0.1%
            'good': 0.3,       # < 0.3%
            'fair': 0.5,       # < 0.5%
            'poor': 1.0        # > 1%
        }

    def _normalize_value(
        self,
        value: float,
        min_val: float,
        max_val: float,
        inverse: bool = False
    ) -> float:
        """
        Normalize a value to 0-100 scale.

        Args:
            value: Value to normalize
            min_val: Minimum value in range
            max_val: Maximum value in range
            inverse: If True, lower values score higher

        Returns:
            Normalized score (0-100)
        """
        if max_val == min_val:
            return 50.0

        normalized = (value - min_val) / (max_val - min_val) * 100
        normalized = max(0, min(100, normalized))

        if inverse:
            normalized = 100 - normalized

        return normalized

    def _calculate_volume_score(self, volume_spike: float) -> Tuple[float, str]:
        """
        Calculate volume spike score component.

        Args:
            volume_spike: Volume relative to average (e.g., 2.0 = 2x average)

        Returns:
            Tuple of (score, factor_description)
        """
        if volume_spike >= self.volume_thresholds['excellent']:
            score = 100.0
            factor = "Exceptional volume surge"
        elif volume_spike >= self.volume_thresholds['good']:
            score = 75.0 + (volume_spike - self.volume_thresholds['good']) / \
                    (self.volume_thresholds['excellent'] - self.volume_thresholds['good']) * 25
            factor = "Strong volume activity"
        elif volume_spike >= self.volume_thresholds['fair']:
            score = 50.0 + (volume_spike - self.volume_thresholds['fair']) / \
                    (self.volume_thresholds['good'] - self.volume_thresholds['fair']) * 25
            factor = "Moderate volume"
        elif volume_spike >= 1.0:
            score = 25.0 + (volume_spike - 1.0) / \
                    (self.volume_thresholds['fair'] - 1.0) * 25
            factor = "Below average volume"
        else:
            score = max(0, 25.0 * volume_spike)
            factor = "Low volume"

        return score, factor

    def _calculate_rsi_macd_score(self, rsi: float, macd_signal: float) -> Tuple[float, str]:
        """
        Calculate RSI/MACD momentum score component.

        Args:
            rsi: Relative Strength Index (0-100)
            macd_signal: MACD histogram value (-100 to 100)

        Returns:
            Tuple of (score, factor_description)
        """
        # RSI ranges: <30 oversold, 30-50 bearish, 50-70 bullish, >70 overbought
        # Ideal RSI for BUY: 50-70 (bullish momentum building)
        # Ideal RSI for momentum stocks: 60-70

        rsi_score = 0.0
        rsi_factor = ""

        if rsi >= 70:
            rsi_score = 80.0  # Overbought but strong
            rsi_factor = "Overbought - Strong momentum"
        elif rsi >= 60:
            rsi_score = 100.0  # Ideal bullish zone
            rsi_factor = "Bullish momentum zone"
        elif rsi >= 50:
            rsi_score = 75.0 + (rsi - 50) * 2.5  # 75-100
            rsi_factor = "Building bullish momentum"
        elif rsi >= 40:
            rsi_score = 50.0 + (rsi - 40) * 2.5  # 50-75
            rsi_factor = "Neutral to slightly bullish"
        elif rsi >= 30:
            rsi_score = 25.0 + (rsi - 30) * 2.5  # 25-50
            rsi_factor = "Bearish zone"
        else:
            rsi_score = max(0, rsi * 0.8)  # Oversold
            rsi_factor = "Oversold - Possible reversal"

        # MACD contribution (0-50 points)
        macd_score = 0.0
        if macd_signal >= 2:
            macd_score = 50.0  # Strong bullish MACD
        elif macd_signal >= 0:
            macd_score = 25.0 + macd_signal * 12.5  # 25-50
        elif macd_signal >= -2:
            macd_score = max(0, 25.0 + macd_signal * 12.5)  # 0-25
        else:
            macd_score = max(0, 12.5 + macd_signal * 6.25)  # Bearish MACD

        # Combined score (RSI 70% + MACD 30%)
        total_score = rsi_score * 0.7 + macd_score * 0.3

        # Factor description
        if macd_signal >= 2:
            factor = f"RSI {rsi:.0f} + Strong MACD"
        elif macd_signal >= 0:
            factor = f"RSI {rsi:.0f} + Bullish MACD"
        else:
            factor = f"RSI {rsi:.0f} + Bearish MACD"

        return total_score, factor

    def _calculate_price_change_score(self, change_pct: float) -> Tuple[float, str]:
        """
        Calculate price change score component.

        Args:
            change_pct: Price change percentage

        Returns:
            Tuple of (score, factor_description)
        """
        # Ideal range is 1-5% change (momentum without overbought/oversold)
        ideal_min = 1.0
        ideal_max = 5.0

        if change_pct >= ideal_min and change_pct <= ideal_max:
            score = 100.0
            factor = "Optimal momentum"
        elif change_pct > ideal_max:
            # Declining score for very high changes (possible overbought)
            excess = change_pct - ideal_max
            score = max(50, 100 - excess * 10)
            factor = "Overbought territory"
        elif change_pct >= 0:
            # Lower score for small changes
            score = 50.0 + (change_pct / ideal_min) * 50
            factor = "Slow movement"
        elif change_pct >= -ideal_min:
            # Negative but small
            score = 50.0 + (change_pct / ideal_min) * 50
            factor = "Slight decline"
        elif change_pct >= -ideal_max:
            # Moderate decline
            score = 50.0 + (change_pct / ideal_max) * 50
            factor = "Moderate decline"
        else:
            # Severe decline
            excess = abs(change_pct) - ideal_max
            score = max(0, 50 - excess * 10)
            factor = "Oversold territory"

        return score, factor

    def _calculate_spread_score(self, spread: float) -> Tuple[float, str]:
        """
        Calculate bid-ask spread score component.

        Args:
            spread: Bid-ask spread as percentage

        Returns:
            Tuple of (score, factor_description)
        """
        if spread <= self.spread_thresholds['excellent']:
            score = 100.0
            factor = "Excellent liquidity"
        elif spread <= self.spread_thresholds['good']:
            score = 75.0 + (self.spread_thresholds['good'] - spread) / \
                    (self.spread_thresholds['good'] - self.spread_thresholds['excellent']) * 25
            factor = "Good liquidity"
        elif spread <= self.spread_thresholds['fair']:
            score = 50.0 + (self.spread_thresholds['fair'] - spread) / \
                    (self.spread_thresholds['fair'] - self.spread_thresholds['good']) * 25
            factor = "Moderate liquidity"
        elif spread <= self.spread_thresholds['poor']:
            score = 25.0 + (self.spread_thresholds['poor'] - spread) / \
                    (self.spread_thresholds['poor'] - self.spread_thresholds['fair']) * 25
            factor = "Low liquidity"
        else:
            score = max(0, 25.0 * (1 - (spread - self.spread_thresholds['poor']) / 2))
            factor = "Very low liquidity"

        return score, factor

    def _calculate_market_cap_score(self, market_cap: float) -> Tuple[float, str]:
        """
        Calculate market capitalization score component.

        Args:
            market_cap: Market cap in IDR

        Returns:
            Tuple of (score, factor_description)
        """
        # Market cap thresholds (in IDR)
        large_cap = 100_000_000_000_000  # 100T
        medium_cap = 10_000_000_000_000   # 10T
        small_cap = 1_000_000_000_000     # 1T

        if market_cap >= large_cap:
            score = 100.0
            factor = "Large cap blue chip"
        elif market_cap >= medium_cap:
            score = 75.0 + (market_cap - medium_cap) / \
                    (large_cap - medium_cap) * 25
            factor = "Mid cap stock"
        elif market_cap >= small_cap:
            score = 50.0 + (market_cap - small_cap) / \
                    (medium_cap - small_cap) * 25
            factor = "Small cap stock"
        else:
            score = max(0, 50.0 * (market_cap / small_cap))
            factor = "Micro cap stock"

        return score, factor

    def _determine_signal(self, score: int) -> SignalType:
        """
        Determine trading signal based on score.

        Args:
            score: Total score (0-100)

        Returns:
            SignalType enum value
        """
        for signal, threshold in sorted(
            self.signal_thresholds.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if score >= threshold:
                return signal
        return SignalType.STRONG_SELL

    def calculate_score(
        self,
        ticker: str,
        name: str,
        price: float,
        change_pct: float,
        volume_spike: float,
        rsi: float = 50.0,
        macd_signal: float = 0.0,
        spread: float = 0.0,
        market_cap: float = 0.0
    ) -> ScoredStock:
        """
        Calculate comprehensive score for a stock.

        Args:
            ticker: Stock ticker symbol
            name: Company name
            price: Current price
            change_pct: Price change percentage
            volume_spike: Volume relative to average
            rsi: Relative Strength Index (0-100), default 50
            macd_signal: MACD histogram value (-100 to 100), default 0
            spread: Bid-ask spread percentage
            market_cap: Market capitalization

        Returns:
            ScoredStock object with complete scoring data
        """
        # Calculate individual component scores
        volume_score, volume_factor = self._calculate_volume_score(volume_spike)
        rsi_macd_score, rsi_macd_factor = self._calculate_rsi_macd_score(rsi, macd_signal)
        price_score, price_factor = self._calculate_price_change_score(change_pct)
        spread_score, spread_factor = self._calculate_spread_score(spread)
        market_cap_score, market_factor = self._calculate_market_cap_score(market_cap)

        # Calculate weighted total score
        total_score = (
            volume_score * (self.weights.get('volume_spike', 25) / 100) +
            rsi_macd_score * (self.weights.get('rsi_macd', 25) / 100) +
            price_score * (self.weights.get('price_change', 20) / 100) +
            spread_score * (self.weights.get('spread', 15) / 100) +
            market_cap_score * (self.weights.get('market_cap', 15) / 100)
        )

        # Round to integer
        total_score = int(round(total_score))
        total_score = max(self.min_score, min(self.max_score, total_score))

        # Determine signal
        signal = self._determine_signal(total_score)

        # Create score breakdown
        breakdown = ScoreBreakdown(
            volume_score=volume_score,
            bo_ratio_score=rsi_macd_score,  # Reuse field name for compatibility
            price_change_score=price_score,
            spread_score=spread_score,
            market_cap_score=market_cap_score,
            total_score=total_score,
            signal=signal,
            score_factors={
                'volume': volume_factor,
                'rsi_macd': rsi_macd_factor,
                'price_change': price_factor,
                'spread': spread_factor,
                'market_cap': market_factor
            }
        )

        return ScoredStock(
            ticker=ticker,
            name=name,
            price=price,
            change_pct=change_pct,
            volume_spike=volume_spike,
            bo_ratio=1.0,  # Legacy field, not used anymore
            spread=spread,
            market_cap=market_cap,
            score=total_score,
            signal=signal,
            score_breakdown=breakdown,
            last_updated=datetime.now()
        )

    def score_batch(
        self,
        stocks_data: List[Dict]
    ) -> List[ScoredStock]:
        """
        Score multiple stocks from raw data.

        Args:
            stocks_data: List of dictionaries with stock data

        Returns:
            List of ScoredStock objects
        """
        scored_stocks = []

        for stock in stocks_data:
            try:
                scored = self.calculate_score(
                    ticker=stock.get('ticker', ''),
                    name=stock.get('name', stock.get('ticker', '')),
                    price=stock.get('price', 0),
                    change_pct=stock.get('change_pct', 0),
                    volume_spike=stock.get('volume_spike', 0),
                    rsi=stock.get('rsi', 50.0),
                    macd_signal=stock.get('macd_signal', 0.0),
                    spread=stock.get('spread', 0),
                    market_cap=stock.get('market_cap', 0)
                )
                scored_stocks.append(scored)
            except Exception as e:
                # Skip stocks that fail scoring
                continue

        return scored_stocks

    def filter_by_score(
        self,
        stocks: List[ScoredStock],
        min_score: int = 50
    ) -> List[ScoredStock]:
        """
        Filter stocks by minimum score threshold.

        Args:
            stocks: List of ScoredStock objects
            min_score: Minimum score threshold

        Returns:
            Filtered list of ScoredStock objects
        """
        return [s for s in stocks if s.score >= min_score]

    def filter_by_signal(
        self,
        stocks: List[ScoredStock],
        signals: List[SignalType]
    ) -> List[ScoredStock]:
        """
        Filter stocks by signal types.

        Args:
            stocks: List of ScoredStock objects
            signals: List of SignalType values to include

        Returns:
            Filtered list of ScoredStock objects
        """
        return [s for s in stocks if s.signal in signals]

    def sort_stocks(
        self,
        stocks: List[ScoredStock],
        by: str = 'score',
        ascending: bool = False
    ) -> List[ScoredStock]:
        """
        Sort stocks by specified criteria.

        Args:
            stocks: List of ScoredStock objects
            by: Sort criteria ('score', 'change_pct', 'volume_spike', 'price')
            ascending: Sort order

        Returns:
            Sorted list of ScoredStock objects
        """
        sort_functions = {
            'score': lambda x: x.score,
            'change_pct': lambda x: x.change_pct,
            'volume_spike': lambda x: x.volume_spike,
            'price': lambda x: x.price,
            'market_cap': lambda x: x.market_cap,
            'ticker': lambda x: x.ticker
        }

        sort_key = sort_functions.get(by, sort_functions['score'])
        return sorted(stocks, key=sort_key, reverse=not ascending)

    def get_top_picks(
        self,
        stocks: List[ScoredStock],
        n: int = 10,
        signal: Optional[SignalType] = None
    ) -> List[ScoredStock]:
        """
        Get top stock picks.

        Args:
            stocks: List of ScoredStock objects
            n: Number of picks to return
            signal: Optional signal filter

        Returns:
            List of top ScoredStock objects
        """
        filtered = stocks
        if signal:
            filtered = self.filter_by_signal(stocks, [signal])

        sorted_stocks = self.sort_stocks(filtered, by='score', ascending=False)
        return sorted_stocks[:n]

    def to_dataframe(self, stocks: List[ScoredStock]) -> pd.DataFrame:
        """
        Convert scored stocks to pandas DataFrame.

        Args:
            stocks: List of ScoredStock objects

        Returns:
            DataFrame with stock data and scores
        """
        data = []
        for stock in stocks:
            data.append({
                'Ticker': stock.ticker,
                'Name': stock.name,
                'Price': stock.price,
                'Change %': stock.change_pct,
                'Volume Spike': stock.volume_spike,
                'BO Ratio': stock.bo_ratio,
                'Spread %': stock.spread,
                'Market Cap': stock.market_cap,
                'Score': stock.score,
                'Signal': stock.signal.value
            })

        return pd.DataFrame(data)


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'ScoringEngine',
    'ScoredStock',
    'ScoreBreakdown',
    'SignalType'
]
