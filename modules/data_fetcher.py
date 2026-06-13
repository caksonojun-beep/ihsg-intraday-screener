"""
IHSG Stock Screener - Data Fetcher Module
==========================================
Handles all data fetching from Yahoo Finance API.
Supports batch fetching, caching, and error handling.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

import pandas as pd
import yfinance as yf
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class StockData:
    """Data class for stock market data."""
    ticker: str
    name: str
    price: float
    change_pct: float
    volume: int
    volume_avg: float
    volume_spike: float
    bid: float
    ask: float
    spread: float
    market_cap: float
    pe_ratio: Optional[float]
    beta: Optional[float]
    fifty_two_week_high: float
    fifty_two_week_low: float
    rsi: float = 50.0  # RSI value (0-100)
    macd_signal: float = 0.0  # MACD histogram value
    last_updated: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


@dataclass
class CandlestickData:
    """Data class for candlestick chart data."""
    timestamp: List[datetime]
    open: List[float]
    high: List[float]
    low: List[float]
    close: List[float]
    volume: List[int]


@dataclass
class BatchFetchResult:
    """Result of batch data fetch operation."""
    stocks: List[StockData]
    errors: List[Dict[str, str]]
    fetch_time: float
    success_count: int
    error_count: int


class DataFetcher:
    """
    Data Fetcher for Indonesian stocks using Yahoo Finance.

    Features:
    - Batch fetching with parallel processing
    - Caching with TTL
    - Retry logic with exponential backoff
    - Error handling and recovery
    """

    def __init__(
        self,
        max_workers: int = 10,
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 300
    ):
        """
        Initialize the Data Fetcher.

        Args:
            max_workers: Maximum parallel workers for batch fetching
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            cache_ttl: Cache time-to-live in seconds
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_ttl = cache_ttl

        # Setup session with retry logic
        self.session = self._create_session()

        # Cache storage
        self._cache: Dict[str, Tuple[Any, datetime]] = {}

    def _create_session(self) -> requests.Session:
        """
        Create a requests session with retry configuration.

        Returns:
            Configured requests session
        """
        session = requests.Session()

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """
        Get data from cache if available and not expired.

        Args:
            key: Cache key

        Returns:
            Cached data or None if expired/missing
        """
        if key in self._cache:
            data, timestamp = self._cache[key]
            if (datetime.now() - timestamp).total_seconds() < self.cache_ttl:
                return data
            else:
                del self._cache[key]
        return None

    def _set_cache(self, key: str, data: Any) -> None:
        """
        Store data in cache with current timestamp.

        Args:
            key: Cache key
            data: Data to cache
        """
        self._cache[key] = (data, datetime.now())

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()

    def fetch_single_stock(self, ticker: str, include_indicators: bool = False) -> StockData:
        """
        Fetch data for a single stock.

        Args:
            ticker: Stock ticker symbol (e.g., 'BBCA.JK')
            include_indicators: If True, calculate RSI/MACD (slower)

        Returns:
            StockData object with market data
        """
        cache_key = f"stock_{ticker}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            # Download stock data using yfinance
            stock = yf.Ticker(ticker)
            info = stock.info

            # Extract relevant data
            price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
            previous_close = info.get('previousClose') or info.get('regularMarketPreviousClose') or price

            # Calculate price change percentage
            if previous_close and previous_close > 0:
                change_pct = ((price - previous_close) / previous_close) * 100
            else:
                change_pct = 0

            # Volume data
            volume = info.get('volume') or 0
            volume_avg = info.get('averageVolume') or volume
            volume_spike = volume / volume_avg if volume_avg > 0 else 0

            # Bid/Ask spread
            bid = info.get('bid') or 0
            ask = info.get('ask') or 0
            if bid > 0 and ask > 0:
                spread = ((ask - bid) / ((ask + bid) / 2)) * 100
            else:
                spread = 0

            # Market cap
            market_cap = info.get('marketCap') or 0

            # Calculate RSI and MACD only if requested (slower)
            if include_indicators:
                rsi = self.calculate_rsi(ticker)
                macd_signal = self.calculate_macd(ticker)
            else:
                rsi = 50.0  # Default neutral
                macd_signal = 0.0

            # Name
            name = info.get('shortName') or info.get('longName') or ticker

            stock_data = StockData(
                ticker=ticker,
                name=name,
                price=price,
                change_pct=change_pct,
                volume=volume,
                volume_avg=volume_avg,
                volume_spike=volume_spike,
                bid=bid,
                ask=ask,
                spread=spread,
                market_cap=market_cap,
                pe_ratio=info.get('trailingPE'),
                beta=info.get('beta'),
                fifty_two_week_high=info.get('fiftyTwoWeekHigh') or price,
                fifty_two_week_low=info.get('fiftyTwoWeekLow') or price,
                rsi=rsi,
                macd_signal=macd_signal,
                last_updated=datetime.now(),
                error=None
            )

            self._set_cache(cache_key, stock_data)
            return stock_data

        except Exception as e:
            return StockData(
                ticker=ticker,
                name=ticker,
                price=0,
                change_pct=0,
                volume=0,
                volume_avg=0,
                volume_spike=0,
                bid=0,
                ask=0,
                spread=0,
                market_cap=0,
                pe_ratio=None,
                beta=None,
                fifty_two_week_high=0,
                fifty_two_week_low=0,
                last_updated=datetime.now(),
                error=str(e)
            )

    def fetch_batch(self, tickers: List[str]) -> BatchFetchResult:
        """
        Fetch data for multiple stocks in parallel.

        Args:
            tickers: List of stock ticker symbols

        Returns:
            BatchFetchResult with all stock data and errors
        """
        start_time = time.time()
        stocks = []
        errors = []

        def fetch_one(ticker: str) -> Tuple[Optional[StockData], Optional[Dict]]:
            try:
                data = self.fetch_single_stock(ticker)
                if data.error:
                    return None, {'ticker': ticker, 'error': data.error}
                return data, None
            except Exception as e:
                return None, {'ticker': ticker, 'error': str(e)}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(fetch_one, ticker): ticker for ticker in tickers}

            for future in as_completed(futures):
                stock_data, error = future.result()
                if stock_data:
                    stocks.append(stock_data)
                if error:
                    errors.append(error)

        fetch_time = time.time() - start_time

        return BatchFetchResult(
            stocks=stocks,
            errors=errors,
            fetch_time=fetch_time,
            success_count=len(stocks),
            error_count=len(errors)
        )

    def fetch_candlestick(
        self,
        ticker: str,
        interval: str = "1d",
        period: str = "1mo"
    ) -> CandlestickData:
        """
        Fetch candlestick data for a stock.

        Args:
            ticker: Stock ticker symbol
            interval: Chart interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1wk)
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)

        Returns:
            CandlestickData object with OHLCV data
        """
        cache_key = f"candle_{ticker}_{interval}_{period}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period, interval=interval)

            if hist.empty:
                return CandlestickData(
                    timestamp=[],
                    open=[],
                    high=[],
                    low=[],
                    close=[],
                    volume=[]
                )

            candle_data = CandlestickData(
                timestamp=hist.index.tolist(),
                open=hist['Open'].tolist(),
                high=hist['High'].tolist(),
                low=hist['Low'].tolist(),
                close=hist['Close'].tolist(),
                volume=hist['Volume'].tolist()
            )

            # Cache for shorter period for candlestick data
            self._cache[cache_key] = (candle_data, datetime.now())

            return candle_data

        except Exception as e:
            return CandlestickData(
                timestamp=[],
                open=[],
                high=[],
                low=[],
                close=[],
                volume=[]
            )

    def fetch_intraday_data(
        self,
        ticker: str,
        interval: str = "5m",
        period: str = "1d"
    ) -> CandlestickData:
        """
        Fetch intraday candlestick data.

        Args:
            ticker: Stock ticker symbol
            interval: Chart interval (1m, 2m, 5m, 15m, 30m, 60m, 90m)
            period: Data period (1d, 5d, 1mo, 3mo)

        Returns:
            CandlestickData object with intraday OHLCV data
        """
        return self.fetch_candlestick(ticker, interval, period)

    def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get detailed stock information.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with detailed stock information
        """
        cache_key = f"info_{ticker}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            self._set_cache(cache_key, info)
            return info

        except Exception as e:
            return {'error': str(e)}

    def calculate_rsi(self, ticker: str, period: int = 14) -> float:
        """
        Calculate RSI (Relative Strength Index) for a stock.

        Args:
            ticker: Stock ticker symbol
            period: RSI period (default 14)

        Returns:
            RSI value (0-100)
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2mo")

            if len(hist) < period + 1:
                return 50.0  # Default neutral RSI

            # Calculate daily returns
            delta = hist['Close'].diff()

            # Separate gains and losses
            gain = delta.where(delta > 0, 0)
            loss = (-delta).where(delta < 0, 0)

            # Calculate average gain and loss
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()

            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

        except Exception:
            return 50.0

    def calculate_macd(self, ticker: str, fast: int = 12, slow: int = 26, signal: int = 9) -> float:
        """
        Calculate MACD histogram for a stock.

        Args:
            ticker: Stock ticker symbol
            fast: Fast EMA period (default 12)
            slow: Slow EMA period (default 26)
            signal: Signal line period (default 9)

        Returns:
            MACD histogram value (can be negative or positive)
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")

            if len(hist) < slow + signal:
                return 0.0

            # Calculate EMAs
            ema_fast = hist['Close'].ewm(span=fast, adjust=False).mean()
            ema_slow = hist['Close'].ewm(span=slow, adjust=False).mean()

            # MACD line
            macd_line = ema_fast - ema_slow

            # Signal line
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()

            # MACD histogram
            macd_histogram = macd_line - signal_line

            # Normalize to percentage of price
            current_price = hist['Close'].iloc[-1]
            macd_pct = (macd_histogram.iloc[-1] / current_price) * 100

            return float(macd_pct) if not pd.isna(macd_pct) else 0.0

        except Exception:
            return 0.0

    def fetch_market_movers(self, tickers: List[str]) -> Dict[str, List[StockData]]:
        """
        Categorize stocks by performance.

        Args:
            tickers: List of stock ticker symbols

        Returns:
            Dictionary with 'gainers', 'losers', and 'active' categories
        """
        result = self.fetch_batch(tickers)
        stocks = result.stocks

        # Sort by change percentage
        sorted_stocks = sorted(stocks, key=lambda x: x.change_pct, reverse=True)

        return {
            'gainers': [s for s in sorted_stocks if s.change_pct > 0][:10],
            'losers': [s for s in sorted_stocks if s.change_pct < 0][-10:][::-1],
            'active': sorted(stocks, key=lambda x: x.volume, reverse=True)[:10]
        }

    def get_market_summary(self, tickers: List[str]) -> Dict[str, Any]:
        """
        Get overall market summary for the given tickers.

        Args:
            tickers: List of stock ticker symbols

        Returns:
            Dictionary with market summary statistics
        """
        result = self.fetch_batch(tickers)

        if not result.stocks:
            return {
                'total_stocks': 0,
                'avg_change': 0,
                'gainers': 0,
                'losers': 0,
                'unchanged': 0,
                'total_volume': 0,
                'fetch_time': result.fetch_time
            }

        gainers = sum(1 for s in result.stocks if s.change_pct > 0)
        losers = sum(1 for s in result.stocks if s.change_pct < 0)
        unchanged = len(result.stocks) - gainers - losers

        return {
            'total_stocks': len(result.stocks),
            'avg_change': sum(s.change_pct for s in result.stocks) / len(result.stocks),
            'gainers': gainers,
            'losers': losers,
            'unchanged': unchanged,
            'total_volume': sum(s.volume for s in result.stocks),
            'fetch_time': result.fetch_time
        }


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'DataFetcher',
    'StockData',
    'CandlestickData',
    'BatchFetchResult'
]
