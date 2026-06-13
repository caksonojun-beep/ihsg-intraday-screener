"""
IHSG Stock Screener - Intraday Detector Module
===============================================
Intraday = Beli Pagi Jual Sore (Buy Morning Sell Afternoon)
Detects stocks suitable for intraday trading strategy.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import pandas as pd


class IntradaySignal(Enum):
    """Enumeration of intraday signal types."""
    STRONG_INTRADAY = "STRONG INTRADAY"
    INTRADAY = "INTRADAY"
    WATCH = "WATCH"
    AVOID = "AVOID"


@dataclass
class IntradayStock:
    """Stock data with intraday analysis."""
    ticker: str
    name: str
    price: float
    change_pct: float
    volume_spike: float
    morning_momentum: float  # Price change in morning session
    morning_volume_ratio: float  # Volume ratio in morning
    intraday_volatility: float  # Intraday price range
    pre_closing_momentum: float  # Last hour momentum
    intraday_score: int  # 0-100
    signal: IntradaySignal
    recommendation: str
    best_entry_window: str  # "08:30-09:00", "09:00-10:00", etc
    best_exit_window: str  # "14:00-14:30", "14:30-15:00", etc
    target_profit: float
    stop_loss: float
    last_updated: datetime


class IntradayDetector:
    """
    Intraday Detector for morning-to-afternoon trading strategy.

    Strategy: Beli Pagi Jual Sore (Buy Morning, Sell Afternoon)
    - Buy window: 08:30 - 10:00 (catch morning momentum)
    - Sell window: 14:00 - 15:30 (sell before close)

    Features:
    - Morning momentum detection
    - Volume analysis
    - Intraday volatility measurement
    - Pre-closing momentum
    - Entry/Exit window recommendations
    """

    def __init__(
        self,
        min_morning_momentum: float = 1.0,
        min_volume_spike: float = 1.5
    ):
        """
        Initialize Intraday Detector.

        Args:
            min_morning_momentum: Minimum price change for morning momentum
            min_volume_spike: Minimum volume spike for morning session
        """
        self.min_morning_momentum = min_morning_momentum
        self.min_volume_spike = min_volume_spike

        # Intraday scoring weights
        self.weights = {
            'morning_momentum': 30.0,
            'morning_volume': 25.0,
            'intraday_volatility': 20.0,
            'pre_closing': 15.0,
            'gap_open': 10.0
        }

        # Score thresholds
        self.score_thresholds = {
            'STRONG_INTRADAY': 75,
            'INTRADAY': 60,
            'WATCH': 45,
            'AVOID': 0
        }

    def _calculate_morning_momentum_score(self, change_pct: float) -> float:
        """
        Calculate morning momentum score.

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

    def _calculate_morning_volume_score(self, volume_spike: float) -> float:
        """
        Calculate morning volume score.

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

    def _calculate_volatility_score(self, volatility: float) -> float:
        """
        Calculate intraday volatility score.

        Args:
            volatility: Intraday price range percentage

        Returns:
            Score 0-100
        """
        # Ideal volatility for intraday is 2-5%
        if 2.0 <= volatility <= 5.0:
            return 100.0
        elif 1.5 <= volatility < 2.0:
            return 75.0
        elif 5.0 < volatility <= 7.0:
            return 75.0
        elif 1.0 <= volatility < 1.5:
            return 50.0
        elif 7.0 < volatility <= 10.0:
            return 50.0
        else:
            return max(0, volatility * 10)

    def _calculate_pre_closing_score(self, pre_closing: float) -> float:
        """
        Calculate pre-closing momentum score.

        Args:
            pre_closing: Price change in last hour

        Returns:
            Score 0-100
        """
        if pre_closing >= 1.0:
            return 100.0
        elif pre_closing >= 0.5:
            return 75.0
        elif pre_closing >= 0:
            return 50.0 + pre_closing * 50
        else:
            return max(0, 50.0 + pre_closing * 50)

    def _calculate_gap_open_score(self, change_pct: float) -> float:
        """
        Calculate gap open score.

        Args:
            change_pct: Price change percentage

        Returns:
            Score 0-100
        """
        # Gap open of 0.5-2% is ideal for intraday
        if 0.5 <= change_pct <= 2.0:
            return 100.0
        elif 0.3 <= change_pct < 0.5:
            return 75.0
        elif 2.0 < change_pct <= 3.0:
            return 75.0
        elif change_pct > 3.0:
            return 50.0  # Too volatile
        else:
            return max(0, change_pct * 100)

    def _determine_signal(self, score: int) -> IntradaySignal:
        """
        Determine intraday signal based on score.

        Args:
            score: Intraday score

        Returns:
            IntradaySignal enum
        """
        if score >= self.score_thresholds['STRONG_INTRADAY']:
            return IntradaySignal.STRONG_INTRADAY
        elif score >= self.score_thresholds['INTRADAY']:
            return IntradaySignal.INTRADAY
        elif score >= self.score_thresholds['WATCH']:
            return IntradaySignal.WATCH
        else:
            return IntradaySignal.AVOID

    def _determine_recommendation(self, score: int) -> str:
        """
        Determine intraday recommendation.

        Args:
            score: Intraday score

        Returns:
            Recommendation string
        """
        if score >= self.score_thresholds['STRONG_INTRADAY']:
            return "STRONG INTRADAY ⭐"
        elif score >= self.score_thresholds['INTRADAY']:
            return "INTRADAY ✅"
        elif score >= self.score_thresholds['WATCH']:
            return "WATCH 👀"
        else:
            return "AVOID ❌"

    def _determine_entry_window(self, change_pct: float) -> str:
        """
        Determine best entry window.

        Args:
            change_pct: Price change percentage

        Returns:
            Entry window string
        """
        if change_pct >= 2.0:
            return "08:30-09:00 (Gap Up)"
        elif change_pct >= 1.0:
            return "09:00-09:30 (Wait Pullback)"
        elif change_pct >= 0:
            return "09:30-10:00 (Confirm Trend)"
        else:
            return "10:00-10:30 (Bottom Pick)"

    def _determine_exit_window(self, change_pct: float) -> str:
        """
        Determine best exit window.

        Args:
            change_pct: Price change percentage

        Returns:
            Exit window string
        """
        if change_pct >= 2.0:
            return "14:00-14:30 (Early Target)"
        elif change_pct >= 1.0:
            return "14:30-15:00 (Optimal)"
        else:
            return "15:00-15:30 (Before Close)"

    def _calculate_target_and_stop(self, price: float, change_pct: float) -> tuple:
        """
        Calculate target profit and stop loss.

        Args:
            price: Current price
            change_pct: Price change percentage

        Returns:
            Tuple of (target_profit, stop_loss) percentages
        """
        # For intraday, target is 1-3%, stop is 1-2%
        if change_pct >= 2.0:
            target = 2.0
            stop = 1.0
        elif change_pct >= 1.0:
            target = 1.5
            stop = 1.0
        else:
            target = 1.0
            stop = 0.5

        return target, stop

    def calculate_intraday_score(
        self,
        ticker: str,
        name: str,
        price: float,
        change_pct: float,
        volume_spike: float,
        morning_momentum: Optional[float] = None,
        morning_volume_ratio: Optional[float] = None,
        intraday_volatility: float = 2.0,
        pre_closing_momentum: float = 0.0
    ) -> IntradayStock:
        """
        Calculate intraday score for a stock.

        Args:
            ticker: Stock ticker
            name: Company name
            price: Current price
            change_pct: Daily price change percentage
            volume_spike: Volume relative to average
            morning_momentum: Morning session momentum (optional)
            morning_volume_ratio: Morning volume ratio (optional)
            intraday_volatility: Intraday price range
            pre_closing_momentum: Pre-closing momentum

        Returns:
            IntradayStock object with analysis
        """
        # Use change_pct as morning momentum if not provided
        if morning_momentum is None:
            morning_momentum = change_pct

        # Use volume_spike as morning volume if not provided
        if morning_volume_ratio is None:
            morning_volume_ratio = volume_spike

        # Calculate individual scores
        morning_score = self._calculate_morning_momentum_score(morning_momentum)
        volume_score = self._calculate_morning_volume_score(morning_volume_ratio)
        volatility_score = self._calculate_volatility_score(intraday_volatility)
        pre_closing_score = self._calculate_pre_closing_score(pre_closing_momentum)
        gap_open_score = self._calculate_gap_open_score(change_pct)

        # Calculate weighted total score
        total_score = (
            morning_score * (self.weights['morning_momentum'] / 100) +
            volume_score * (self.weights['morning_volume'] / 100) +
            volatility_score * (self.weights['intraday_volatility'] / 100) +
            pre_closing_score * (self.weights['pre_closing'] / 100) +
            gap_open_score * (self.weights['gap_open'] / 100)
        )

        # Round to integer
        total_score = int(round(total_score))
        total_score = max(0, min(100, total_score))

        # Determine signal and recommendation
        signal = self._determine_signal(total_score)
        recommendation = self._determine_recommendation(total_score)

        # Determine entry/exit windows
        entry_window = self._determine_entry_window(change_pct)
        exit_window = self._determine_exit_window(change_pct)

        # Calculate target and stop
        target_profit, stop_loss = self._calculate_target_and_stop(price, change_pct)

        return IntradayStock(
            ticker=ticker,
            name=name,
            price=price,
            change_pct=change_pct,
            volume_spike=volume_spike,
            morning_momentum=morning_momentum,
            morning_volume_ratio=morning_volume_ratio,
            intraday_volatility=intraday_volatility,
            pre_closing_momentum=pre_closing_momentum,
            intraday_score=total_score,
            signal=signal,
            recommendation=recommendation,
            best_entry_window=entry_window,
            best_exit_window=exit_window,
            target_profit=target_profit,
            stop_loss=stop_loss,
            last_updated=datetime.now()
        )

    def analyze_batch(
        self,
        stocks_data: List[Dict]
    ) -> List[IntradayStock]:
        """
        Analyze multiple stocks for intraday strategy.

        Args:
            stocks_data: List of stock data dictionaries

        Returns:
            List of IntradayStock objects
        """
        results = []

        for stock in stocks_data:
            try:
                intraday_stock = self.calculate_intraday_score(
                    ticker=stock.get('ticker', ''),
                    name=stock.get('name', stock.get('ticker', '')),
                    price=stock.get('price', 0),
                    change_pct=stock.get('change_pct', 0),
                    volume_spike=stock.get('volume_spike', 0),
                    morning_momentum=stock.get('morning_momentum'),
                    morning_volume_ratio=stock.get('morning_volume_ratio'),
                    intraday_volatility=stock.get('intraday_volatility', 2.0),
                    pre_closing_momentum=stock.get('pre_closing_momentum', 0)
                )
                results.append(intraday_stock)
            except Exception:
                continue

        return results

    def filter_intraday_stocks(
        self,
        stocks: List[IntradayStock],
        min_score: int = 60,
        min_change: float = 0.5
    ) -> List[IntradayStock]:
        """
        Filter intraday stocks by criteria.

        Args:
            stocks: List of IntradayStock objects
            min_score: Minimum intraday score
            min_change: Minimum price change percentage

        Returns:
            Filtered list of IntradayStock objects
        """
        filtered = [s for s in stocks if s.intraday_score >= min_score]

        if min_change > 0:
            filtered = [s for s in filtered if s.change_pct >= min_change]

        return filtered

    def get_top_intraday_picks(
        self,
        stocks: List[IntradayStock],
        n: int = 10,
        signal: Optional[IntradaySignal] = None
    ) -> List[IntradayStock]:
        """
        Get top intraday stock picks.

        Args:
            stocks: List of IntradayStock objects
            n: Number of picks to return
            signal: Filter by signal type

        Returns:
            List of top IntradayStock objects
        """
        filtered = stocks

        if signal:
            filtered = [s for s in filtered if s.signal == signal]

        # Sort by intraday score
        sorted_stocks = sorted(filtered, key=lambda x: x.intraday_score, reverse=True)
        return sorted_stocks[:n]

    def to_dataframe(self, stocks: List[IntradayStock]) -> pd.DataFrame:
        """
        Convert intraday stocks to DataFrame.

        Args:
            stocks: List of IntradayStock objects

        Returns:
            DataFrame with intraday data
        """
        data = []
        for stock in stocks:
            data.append({
                'Ticker': stock.ticker,
                'Name': stock.name[:30] + '...' if len(stock.name) > 30 else stock.name,
                'Price': f"IDR {stock.price:,.0f}",
                'Change %': stock.change_pct,
                'Volume Spike': f"{stock.volume_spike:.2f}x",
                'Intraday Score': stock.intraday_score,
                'Entry': stock.best_entry_window,
                'Exit': stock.best_exit_window,
                'Recommendation': stock.recommendation
            })

        return pd.DataFrame(data)


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'IntradayDetector',
    'IntradayStock',
    'IntradaySignal'
]
