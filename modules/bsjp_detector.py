"""
IHSG Stock Screener - BSJP Detector Module
==========================================
BSJP = Beli Sore Jual Pagi (Buy Afternoon Sell Morning)
Detects stocks suitable for overnight trading strategy.
"""

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
import pandas as pd


class GapType(Enum):
    """Enumeration of gap types."""
    GAP_UP = "GAP UP"
    GAP_DOWN = "GAP DOWN"
    NO_GAP = "NO GAP"
    UNKNOWN = "UNKNOWN"


@dataclass
class BSJPStock:
    """Stock data with BSJP analysis."""
    ticker: str
    name: str
    price: float
    change_pct: float
    volume_spike: float
    closing_momentum: float  # Price change in last hour
    closing_volume_ratio: float  # Volume in last hour vs average
    gap_potential: float  # Potential gap up/down next day
    after_hours_change: float  # After hours price movement
    pre_market_change: float  # Pre-market indication
    bsjp_score: int  # 0-100 BSJP score
    gap_type: GapType
    recommendation: str  # "STRONG BSJP", "BSJP", "WATCH", "AVOID"
    last_updated: datetime


class BSJPDetector:
    """
    BSJP Detector for overnight trading strategy.

    Strategy: Beli Sore Jual Pagi (Buy Afternoon, Sell Morning)
    - Buy window: 14:30 - 15:50 WIB
    - Sell window: 08:30 - 09:30 WIB next day

    Features:
    - Closing momentum detection
    - Gap potential analysis
    - After hours activity tracking
    - Pre-market indication
    - BSJP score calculation
    """

    def __init__(
        self,
        gap_up_threshold: float = 1.0,
        gap_down_threshold: float = -1.0,
        closing_volume_spike_min: float = 1.5,
        closing_price_momentum_min: float = 1.0
    ):
        """
        Initialize BSJP Detector.

        Args:
            gap_up_threshold: Minimum % for gap up detection
            gap_down_threshold: Maximum % for gap down detection
            closing_volume_spike_min: Minimum volume spike for closing
            closing_price_momentum_min: Minimum price change for momentum
        """
        self.gap_up_threshold = gap_up_threshold
        self.gap_down_threshold = gap_down_threshold
        self.closing_volume_spike_min = closing_volume_spike_min
        self.closing_price_momentum_min = closing_price_momentum_min

        # BSJP scoring weights
        self.weights = {
            'closing_momentum': 30.0,
            'closing_volume': 25.0,
            'overnight_gap': 20.0,
            'after_hours_activity': 15.0,
            'pre_market': 10.0
        }

        # Score thresholds
        self.score_thresholds = {
            'STRONG_BSJP': 75,
            'BSJP': 60,
            'WATCH': 45,
            'AVOID': 0
        }

    def _calculate_closing_momentum_score(self, change_pct: float) -> float:
        """
        Calculate closing momentum score.

        Args:
            change_pct: Price change percentage

        Returns:
            Score 0-100
        """
        if change_pct >= 3.0:
            return 100.0
        elif change_pct >= 2.0:
            return 80.0 + (change_pct - 2.0) * 20
        elif change_pct >= 1.0:
            return 60.0 + (change_pct - 1.0) * 20
        elif change_pct >= 0.5:
            return 40.0 + (change_pct - 0.5) * 40
        elif change_pct >= 0:
            return 20.0 + change_pct * 40
        else:
            return max(0, 20.0 + change_pct * 20)

    def _calculate_closing_volume_score(self, volume_spike: float) -> float:
        """
        Calculate closing volume score.

        Args:
            volume_spike: Volume relative to average

        Returns:
            Score 0-100
        """
        if volume_spike >= 3.0:
            return 100.0
        elif volume_spike >= 2.0:
            return 75.0 + (volume_spike - 2.0) * 25
        elif volume_spike >= 1.5:
            return 50.0 + (volume_spike - 1.5) * 50
        elif volume_spike >= 1.0:
            return 25.0 + (volume_spike - 1.0) * 50
        else:
            return max(0, volume_spike * 25)

    def _calculate_gap_potential_score(self, change_pct: float) -> float:
        """
        Calculate overnight gap potential score.

        Args:
            change_pct: Price change percentage

        Returns:
            Score 0-100
        """
        # Higher momentum = higher gap potential
        if change_pct >= 3.0:
            return 100.0
        elif change_pct >= 2.0:
            return 80.0
        elif change_pct >= 1.5:
            return 70.0
        elif change_pct >= 1.0:
            return 60.0
        elif change_pct >= 0.5:
            return 50.0
        else:
            return max(0, change_pct * 100)

    def _calculate_after_hours_score(self, after_hours_change: float) -> float:
        """
        Calculate after hours activity score.

        Args:
            after_hours_change: After hours price change

        Returns:
            Score 0-100
        """
        if after_hours_change >= 1.0:
            return 100.0
        elif after_hours_change >= 0.5:
            return 75.0
        elif after_hours_change >= 0:
            return 50.0 + after_hours_change * 50
        else:
            return max(0, 50.0 + after_hours_change * 50)

    def _calculate_pre_market_score(self, pre_market_change: float) -> float:
        """
        Calculate pre-market indication score.

        Args:
            pre_market_change: Pre-market price change

        Returns:
            Score 0-100
        """
        if pre_market_change >= 1.0:
            return 100.0
        elif pre_market_change >= 0.5:
            return 75.0
        elif pre_market_change >= 0:
            return 50.0 + pre_market_change * 50
        else:
            return max(0, 50.0 + pre_market_change * 50)

    def _determine_gap_type(self, change_pct: float) -> GapType:
        """
        Determine gap type based on price change.

        Args:
            change_pct: Price change percentage

        Returns:
            GapType enum
        """
        if change_pct >= self.gap_up_threshold:
            return GapType.GAP_UP
        elif change_pct <= self.gap_down_threshold:
            return GapType.GAP_DOWN
        else:
            return GapType.NO_GAP

    def _determine_recommendation(self, score: int) -> str:
        """
        Determine BSJP recommendation based on score.

        Args:
            score: BSJP score

        Returns:
            Recommendation string
        """
        if score >= self.score_thresholds['STRONG_BSJP']:
            return "STRONG BSJP ⭐"
        elif score >= self.score_thresholds['BSJP']:
            return "BSJP ✅"
        elif score >= self.score_thresholds['WATCH']:
            return "WATCH 👀"
        else:
            return "AVOID ❌"

    def calculate_bsjp_score(
        self,
        ticker: str,
        name: str,
        price: float,
        change_pct: float,
        volume_spike: float,
        closing_momentum: Optional[float] = None,
        closing_volume_ratio: Optional[float] = None,
        after_hours_change: float = 0.0,
        pre_market_change: float = 0.0
    ) -> BSJPStock:
        """
        Calculate BSJP score for a stock.

        Args:
            ticker: Stock ticker
            name: Company name
            price: Current price
            change_pct: Daily price change percentage
            volume_spike: Volume relative to average
            closing_momentum: Price change in last hour (optional)
            closing_volume_ratio: Volume ratio in last hour (optional)
            after_hours_change: After hours price change
            pre_market_change: Pre-market price change

        Returns:
            BSJPStock object with analysis
        """
        # Use change_pct as closing momentum if not provided
        if closing_momentum is None:
            closing_momentum = change_pct

        # Use volume_spike as closing volume if not provided
        if closing_volume_ratio is None:
            closing_volume_ratio = volume_spike

        # Calculate individual scores
        closing_momentum_score = self._calculate_closing_momentum_score(closing_momentum)
        closing_volume_score = self._calculate_closing_volume_score(closing_volume_ratio)
        gap_potential_score = self._calculate_gap_potential_score(change_pct)
        after_hours_score = self._calculate_after_hours_score(after_hours_change)
        pre_market_score = self._calculate_pre_market_score(pre_market_change)

        # Calculate weighted total score
        total_score = (
            closing_momentum_score * (self.weights['closing_momentum'] / 100) +
            closing_volume_score * (self.weights['closing_volume'] / 100) +
            gap_potential_score * (self.weights['overnight_gap'] / 100) +
            after_hours_score * (self.weights['after_hours_activity'] / 100) +
            pre_market_score * (self.weights['pre_market'] / 100)
        )

        # Round to integer
        total_score = int(round(total_score))
        total_score = max(0, min(100, total_score))

        # Determine gap type and recommendation
        gap_type = self._determine_gap_type(change_pct)
        recommendation = self._determine_recommendation(total_score)

        return BSJPStock(
            ticker=ticker,
            name=name,
            price=price,
            change_pct=change_pct,
            volume_spike=volume_spike,
            closing_momentum=closing_momentum,
            closing_volume_ratio=closing_volume_ratio,
            gap_potential=gap_potential_score,
            after_hours_change=after_hours_change,
            pre_market_change=pre_market_change,
            bsjp_score=total_score,
            gap_type=gap_type,
            recommendation=recommendation,
            last_updated=datetime.now()
        )

    def analyze_batch(
        self,
        stocks_data: List[Dict]
    ) -> List[BSJPStock]:
        """
        Analyze multiple stocks for BSJP strategy.

        Args:
            stocks_data: List of stock data dictionaries

        Returns:
            List of BSJPStock objects
        """
        results = []

        for stock in stocks_data:
            try:
                bsjp_stock = self.calculate_bsjp_score(
                    ticker=stock.get('ticker', ''),
                    name=stock.get('name', stock.get('ticker', '')),
                    price=stock.get('price', 0),
                    change_pct=stock.get('change_pct', 0),
                    volume_spike=stock.get('volume_spike', 0),
                    closing_momentum=stock.get('closing_momentum'),
                    closing_volume_ratio=stock.get('closing_volume_ratio'),
                    after_hours_change=stock.get('after_hours_change', 0),
                    pre_market_change=stock.get('pre_market_change', 0)
                )
                results.append(bsjp_stock)
            except Exception:
                continue

        return results

    def filter_bsjp_stocks(
        self,
        stocks: List[BSJPStock],
        min_score: int = 60,
        min_change: float = 1.0,
        gap_types: Optional[List[GapType]] = None
    ) -> List[BSJPStock]:
        """
        Filter BSJP stocks by criteria.

        Args:
            stocks: List of BSJPStock objects
            min_score: Minimum BSJP score
            min_change: Minimum price change percentage
            gap_types: List of GapType to include

        Returns:
            Filtered list of BSJPStock objects
        """
        filtered = [s for s in stocks if s.bsjp_score >= min_score]

        if min_change > 0:
            filtered = [s for s in filtered if s.change_pct >= min_change]

        if gap_types:
            filtered = [s for s in filtered if s.gap_type in gap_types]

        return filtered

    def get_top_bsjp_picks(
        self,
        stocks: List[BSJPStock],
        n: int = 10,
        recommendation: Optional[str] = None
    ) -> List[BSJPStock]:
        """
        Get top BSJP stock picks.

        Args:
            stocks: List of BSJPStock objects
            n: Number of picks to return
            recommendation: Filter by recommendation type

        Returns:
            List of top BSJPStock objects
        """
        filtered = stocks

        if recommendation:
            filtered = [s for s in filtered if s.recommendation == recommendation]

        # Sort by BSJP score
        sorted_stocks = sorted(filtered, key=lambda x: x.bsjp_score, reverse=True)
        return sorted_stocks[:n]

    def get_gap_stocks(
        self,
        stocks: List[BSJPStock],
        gap_type: GapType
    ) -> List[BSJPStock]:
        """
        Get stocks by gap type.

        Args:
            stocks: List of BSJPStock objects
            gap_type: GapType to filter

        Returns:
            List of gap stocks
        """
        return [s for s in stocks if s.gap_type == gap_type]

    def to_dataframe(self, stocks: List[BSJPStock]) -> pd.DataFrame:
        """
        Convert BSJP stocks to DataFrame.

        Args:
            stocks: List of BSJPStock objects

        Returns:
            DataFrame with BSJP data
        """
        data = []
        for stock in stocks:
            data.append({
                'Ticker': stock.ticker,
                'Name': stock.name[:30] + '...' if len(stock.name) > 30 else stock.name,
                'Price': f"IDR {stock.price:,.0f}",
                'Change %': stock.change_pct,
                'Volume Spike': f"{stock.volume_spike:.2f}x",
                'BSJP Score': stock.bsjp_score,
                'Gap Type': stock.gap_type.value,
                'Recommendation': stock.recommendation
            })

        return pd.DataFrame(data)


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'BSJPDetector',
    'BSJPStock',
    'GapType'
]
