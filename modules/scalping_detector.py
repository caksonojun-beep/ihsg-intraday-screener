"""
IHSG Stock Screener - Scalping Detector Module
==============================================
Scalping = Beli Pagi Jual Sore (Buy Morning Sell Afternoon)
Detects stocks suitable for scalping trading strategy.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import pandas as pd


class ScalpingSignal(Enum):
    """Enumeration of scalping signal types."""
    STRONG_SCALPING = "STRONG SCALPING"
    SCALPING = "SCALPING"
    WATCH = "WATCH"
    AVOID = "AVOID"


@dataclass
class ScalpingStock:
    """Stock data with scalping analysis."""
    ticker: str
    name: str
    price: float
    change_pct: float
    volume_spike: float
    morning_momentum: float
    morning_volume_ratio: float
    scalping_volatility: float
    pre_closing_momentum: float
    scalping_score: int
    signal: ScalpingSignal
    recommendation: str
    best_entry_window: str
    best_exit_window: str
    target_profit: float
    stop_loss: float
    last_updated: datetime


class ScalpingDetector:
    """
    Scalping Detector for morning-to-afternoon trading strategy.

    Strategy: Beli Pagi Jual Sore (Buy Morning, Sell Afternoon)
    - Buy window: 08:30 - 10:00 (catch morning momentum)
    - Sell window: 14:00 - 15:30 (sell before close)
    """

    def __init__(
        self,
        min_morning_momentum: float = 1.0,
        min_volume_spike: float = 1.5
    ):
        self.min_morning_momentum = min_morning_momentum
        self.min_volume_spike = min_volume_spike

        self.weights = {
            'morning_momentum': 30.0,
            'morning_volume': 25.0,
            'scalping_volatility': 20.0,
            'pre_closing': 15.0,
            'gap_open': 10.0
        }

        self.score_thresholds = {
            'STRONG_SCALPING': 75,
            'SCALPING': 60,
            'WATCH': 45,
            'AVOID': 0
        }

    def _calculate_morning_momentum_score(self, change_pct: float) -> float:
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
        if pre_closing >= 1.0:
            return 100.0
        elif pre_closing >= 0.5:
            return 75.0
        elif pre_closing >= 0:
            return 50.0 + pre_closing * 50
        else:
            return max(0, 50.0 + pre_closing * 50)

    def _calculate_gap_open_score(self, change_pct: float) -> float:
        if 0.5 <= change_pct <= 2.0:
            return 100.0
        elif 0.3 <= change_pct < 0.5:
            return 75.0
        elif 2.0 < change_pct <= 3.0:
            return 75.0
        elif change_pct > 3.0:
            return 50.0
        else:
            return max(0, change_pct * 100)

    def _determine_signal(self, score: int) -> ScalpingSignal:
        if score >= self.score_thresholds['STRONG_SCALPING']:
            return ScalpingSignal.STRONG_SCALPING
        elif score >= self.score_thresholds['SCALPING']:
            return ScalpingSignal.SCALPING
        elif score >= self.score_thresholds['WATCH']:
            return ScalpingSignal.WATCH
        else:
            return ScalpingSignal.AVOID

    def _determine_recommendation(self, score: int) -> str:
        if score >= self.score_thresholds['STRONG_SCALPING']:
            return "STRONG SCALPING ⭐"
        elif score >= self.score_thresholds['SCALPING']:
            return "SCALPING ✅"
        elif score >= self.score_thresholds['WATCH']:
            return "WATCH 👀"
        else:
            return "AVOID ❌"

    def _determine_entry_window(self, change_pct: float) -> str:
        if change_pct >= 2.0:
            return "08:30-09:00 (Gap Up)"
        elif change_pct >= 1.0:
            return "09:00-09:30 (Wait Pullback)"
        elif change_pct >= 0:
            return "09:30-10:00 (Confirm Trend)"
        else:
            return "10:00-10:30 (Bottom Pick)"

    def _determine_exit_window(self, change_pct: float) -> str:
        if change_pct >= 2.0:
            return "14:00-14:30 (Early Target)"
        elif change_pct >= 1.0:
            return "14:30-15:00 (Optimal)"
        else:
            return "15:00-15:30 (Before Close)"

    def _calculate_target_and_stop(self, price: float, change_pct: float) -> tuple:
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

    def calculate_scalping_score(
        self,
        ticker: str,
        name: str,
        price: float,
        change_pct: float,
        volume_spike: float,
        morning_momentum: Optional[float] = None,
        morning_volume_ratio: Optional[float] = None,
        scalping_volatility: float = 2.0,
        pre_closing_momentum: float = 0.0
    ) -> ScalpingStock:
        if morning_momentum is None:
            morning_momentum = change_pct
        if morning_volume_ratio is None:
            morning_volume_ratio = volume_spike

        morning_score = self._calculate_morning_momentum_score(morning_momentum)
        volume_score = self._calculate_morning_volume_score(morning_volume_ratio)
        volatility_score = self._calculate_volatility_score(scalping_volatility)
        pre_closing_score = self._calculate_pre_closing_score(pre_closing_momentum)
        gap_open_score = self._calculate_gap_open_score(change_pct)

        total_score = (
            morning_score * (self.weights['morning_momentum'] / 100) +
            volume_score * (self.weights['morning_volume'] / 100) +
            volatility_score * (self.weights['scalping_volatility'] / 100) +
            pre_closing_score * (self.weights['pre_closing'] / 100) +
            gap_open_score * (self.weights['gap_open'] / 100)
        )

        total_score = int(round(total_score))
        total_score = max(0, min(100, total_score))

        signal = self._determine_signal(total_score)
        recommendation = self._determine_recommendation(total_score)
        entry_window = self._determine_entry_window(change_pct)
        exit_window = self._determine_exit_window(change_pct)
        target_profit, stop_loss = self._calculate_target_and_stop(price, change_pct)

        return ScalpingStock(
            ticker=ticker,
            name=name,
            price=price,
            change_pct=change_pct,
            volume_spike=volume_spike,
            morning_momentum=morning_momentum,
            morning_volume_ratio=morning_volume_ratio,
            scalping_volatility=scalping_volatility,
            pre_closing_momentum=pre_closing_momentum,
            scalping_score=total_score,
            signal=signal,
            recommendation=recommendation,
            best_entry_window=entry_window,
            best_exit_window=exit_window,
            target_profit=target_profit,
            stop_loss=stop_loss,
            last_updated=datetime.now()
        )

    def analyze_batch(self, stocks_data: List[Dict]) -> List[ScalpingStock]:
        results = []
        for stock in stocks_data:
            try:
                scalping_stock = self.calculate_scalping_score(
                    ticker=stock.get('ticker', ''),
                    name=stock.get('name', stock.get('ticker', '')),
                    price=stock.get('price', 0),
                    change_pct=stock.get('change_pct', 0),
                    volume_spike=stock.get('volume_spike', 0),
                    morning_momentum=stock.get('morning_momentum'),
                    morning_volume_ratio=stock.get('morning_volume_ratio'),
                    scalping_volatility=stock.get('scalping_volatility', 2.0),
                    pre_closing_momentum=stock.get('pre_closing_momentum', 0)
                )
                results.append(scalping_stock)
            except Exception:
                continue
        return results

    def filter_scalping_stocks(
        self,
        stocks: List[ScalpingStock],
        min_score: int = 60,
        min_change: float = 0.5
    ) -> List[ScalpingStock]:
        filtered = [s for s in stocks if s.scalping_score >= min_score]
        if min_change > 0:
            filtered = [s for s in filtered if s.change_pct >= min_change]
        return filtered

    def get_top_scalping_picks(
        self,
        stocks: List[ScalpingStock],
        n: int = 10,
        signal: Optional[ScalpingSignal] = None
    ) -> List[ScalpingStock]:
        filtered = stocks
        if signal:
            filtered = [s for s in filtered if s.signal == signal]
        sorted_stocks = sorted(filtered, key=lambda x: x.scalping_score, reverse=True)
        return sorted_stocks[:n]

    def to_dataframe(self, stocks: List[ScalpingStock]) -> pd.DataFrame:
        data = []
        for stock in stocks:
            data.append({
                'Ticker': stock.ticker,
                'Name': stock.name[:30] + '...' if len(stock.name) > 30 else stock.name,
                'Price': f"IDR {stock.price:,.0f}",
                'Change %': stock.change_pct,
                'Volume Spike': f"{stock.volume_spike:.2f}x",
                'Scalping Score': stock.scalping_score,
                'Entry': stock.best_entry_window,
                'Exit': stock.best_exit_window,
                'Recommendation': stock.recommendation
            })
        return pd.DataFrame(data)


__all__ = [
    'ScalpingDetector',
    'ScalpingStock',
    'ScalpingSignal'
]
