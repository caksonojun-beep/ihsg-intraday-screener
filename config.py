"""
IHSG Stock Screener - Configuration Module
==========================================
Contains all configuration settings, constants, and environment variables.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, time


# ============================================================================
# MARKET SESSION CONFIGURATION
# ============================================================================

@dataclass
class SessionConfig:
    """Configuration for trading session detection."""

    # Jakarta timezone offset (WIB) is UTC+7
    TIMEZONE_OFFSET: int = 7

    # Regular trading hours (WIB)
    PRE_MARKET_START: time = field(default_factory=lambda: time(7, 0))   # 07:00 WIB
    REGULAR_START: time = field(default_factory=lambda: time(8, 30))    # 08:30 WIB
    REGULAR_END: time = field(default_factory=lambda: time(15, 30))     # 15:30 WIB
    AFTER_HOURS_END: time = field(default_factory=lambda: time(15, 50)) # 15:50 WIB

    # Session status messages
    SESSION_STATUS: Dict[str, str] = field(default_factory=lambda: {
        'pre_market': 'Pre-Market',
        'open': 'Regular Session',
        'after_hours': 'After Hours',
        'closed': 'Market Closed',
        'weekend': 'Weekend',
        'holiday': 'Holiday'
    })


# ============================================================================
# SCORING ENGINE CONFIGURATION
# ============================================================================

@dataclass
class ScoringConfig:
    """Configuration for stock scoring algorithm."""

    # Score weights (must sum to 100)
    weights: Dict[str, float] = field(default_factory=lambda: {
        'volume_spike': 25.0,    # Volume anomaly weight
        'rsi_macd': 25.0,        # RSI/MACD momentum weight
        'price_change': 20.0,     # Price movement weight
        'spread': 15.0,           # Bid-ask spread weight
        'market_cap': 15.0       # Market capitalization weight
    })

    # Alias for backward compatibility
    WEIGHTS = property(lambda self: self.weights)

    # Score thresholds
    MIN_SCORE: int = 50
    MAX_SCORE: int = 100

    # Volume spike thresholds
    VOLUME_SPIKE_THRESHOLD: float = 2.0  # 2x average volume
    VOLUME_SPIKE_EXCELLENT: float = 3.0  # 3x average volume

    # Buy/Order ratio thresholds
    BO_RATIO_MIN: float = 1.0
    BO_RATIO_EXCELLENT: float = 1.5

    # Spread thresholds (as percentage of price)
    SPREAD_EXCELLENT: float = 0.1  # < 0.1%
    SPREAD_GOOD: float = 0.3       # < 0.3%
    SPREAD_FAIR: float = 0.5       # < 0.5%

    # Market cap thresholds (in IDR)
    MARKET_CAP_LARGE: float = 100_000_000_000_000  # 100T IDR
    MARKET_CAP_MEDIUM: float = 10_000_000_000_000  # 10T IDR
    MARKET_CAP_SMALL: float = 1_000_000_000_000     # 1T IDR


# ============================================================================
# BSJP (Beli Sore Jual Pagi) CONFIGURATION
# ============================================================================

@dataclass
class BSJPConfig:
    """Configuration for BSJP (Overnight Trading) strategy."""

    # BSJP session hours (WIB)
    BSJP_BUY_WINDOW_START: time = field(default_factory=lambda: time(14, 30))  # 14:30 WIB
    BSJP_BUY_WINDOW_END: time = field(default_factory=lambda: time(15, 50))    # 15:50 WIB
    BSJP_SELL_WINDOW_START: time = field(default_factory=lambda: time(8, 30)) # 08:30 WIB
    BSJP_SELL_WINDOW_END: time = field(default_factory=lambda: time(9, 30))  # 09:30 WIB

    # Gap thresholds
    GAP_UP_THRESHOLD: float = 1.0   # > 1% gap up
    GAP_DOWN_THRESHOLD: float = -1.0 # < -1% gap down

    # Closing momentum thresholds
    CLOSING_VOLUME_SPIKE_MIN: float = 1.5  # 1.5x average volume at closing
    CLOSING_PRICE_MOMENTUM_MIN: float = 1.0  # > 1% price increase at closing

    # BSJP scoring weights
    BSJP_WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        'closing_momentum': 30.0,    # Price increase in last hour
        'closing_volume': 25.0,      # Volume spike at closing
        'overnight_gap': 20.0,       # Potential gap up next day
        'after_hours_activity': 15.0, # After hours price movement
        'pre_market': 10.0          # Pre-market indication
    })


# ============================================================================
# RECOMMENDATION ENGINE CONFIGURATION
# ============================================================================

@dataclass
class RecommendationConfig:
    """Configuration for trading recommendations."""

    # Risk-reward ratios
    DEFAULT_RISK_REWARD: float = 2.0
    MIN_RISK_REWARD: float = 1.5

    # Stop loss percentages
    STOP_LOSS_TIGHT: float = 2.0   # 2% from entry
    STOP_LOSS_NORMAL: float = 5.0  # 5% from entry
    STOP_LOSS_WIDE: float = 8.0    # 8% from entry

    # Target profit percentages
    TARGET_AGGRESSIVE: float = 10.0  # 10% from entry
    TARGET_MODERATE: float = 5.0      # 5% from entry
    TARGET_CONSERVATIVE: float = 3.0 # 3% from entry

    # Signal thresholds
    SIGNAL_BUY: str = 'BUY'
    SIGNAL_HOLD: str = 'HOLD'
    SIGNAL_SELL: str = 'SELL'
    SIGNAL_STRONG_BUY: str = 'STRONG BUY'
    SIGNAL_STRONG_SELL: str = 'STRONG SELL'


# ============================================================================
# DATA SOURCE CONFIGURATION
# ============================================================================

@dataclass
class DataSourceConfig:
    """Configuration for data fetching."""

    # Yahoo Finance settings
    YAHOO_BASE_URL: str = "https://query1.finance.yahoo.com/v8/finance"
    YAHOO_CHART_URL: str = "https://query1.finance.yahoo.com/v8/finance/chart"

    # Default parameters
    DEFAULT_INTERVAL: str = "1d"
    DEFAULT_PERIOD: str = "1mo"

    # Candlestick intervals
    INTERVALS: List[str] = field(default_factory=lambda: [
        "1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1wk"
    ])

    # Period options
    PERIODS: Dict[str, str] = field(default_factory=lambda: {
        "1 Week": "5d",
        "1 Month": "1mo",
        "3 Months": "3mo",
        "6 Months": "6mo",
        "1 Year": "1y",
        "2 Years": "2y",
        "5 Years": "5y",
        "Max": "max"
    })

    # Retry configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0  # seconds
    TIMEOUT: int = 30  # seconds


# ============================================================================
# UI CONFIGURATION
# ============================================================================

@dataclass
class UIConfig:
    """Configuration for UI settings."""

    # Theme
    THEME: str = "dark"
    PRIMARY_COLOR: str = "#00D4AA"
    SECONDARY_COLOR: str = "#1E88E5"
    ACCENT_COLOR: str = "#FF6B6B"

    # Table settings
    PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Cache settings
    CACHE_TTL: int = 300  # 5 minutes
    SESSION_CACHE_TTL: int = 60  # 1 minute for session data

    # Refresh settings
    AUTO_REFRESH_DEFAULT: bool = False
    AUTO_REFRESH_INTERVAL: int = 60  # seconds


# ============================================================================
# WATCHLIST CONFIGURATION
# ============================================================================

@dataclass
class WatchlistConfig:
    """Configuration for stock watchlist."""

    # Default IHSG watchlist (top stocks by market cap)
    DEFAULT_TICKERS: List[str] = field(default_factory=lambda: [
        # Large Cap - Banking
        "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BDMN.JK",
        # Large Cap - Consumer
        "UNVR.JK", "ICBP.JK", "INDF.JK", "KLBF.JK", "HMSP.JK",
        # Large Cap - Mining
        "ANTM.JK", "TINS.JK", "PTBA.JK", "ADRO.JK", "ITMG.JK",
        # Large Cap - Property
        "BSDE.JK", "PWON.JK", "SMRA.JK", "CTRA.JK", "LPKR.JK",
        # Large Cap - Manufacturing
        "ASII.JK", "GJTL.JK", "IMAS.JK", "次日.JK", "RALS.JK",
        # Large Cap -Telecom
        "TLKM.JK", "EXCL.JK", "FREN.JK",
        # Large Cap - Utilities
        "PGAS.JK", "PTUN.JK",
        # Large Cap - Automotive
        "ASSA.JK", "MAPB.JK",
        # Additional movers
        "AMZN.JK", "GOTO.JK", "BUKA.JK"
    ])

    # Group categories
    TICKER_GROUPS: Dict[str, List[str]] = field(default_factory=lambda: {
        "Banking": ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BDMN.JK", "BTPN.JK", "NISP.JK", "BJBR.JK", "BJTM.JK", "BRIS.JK", "BNGA.JK", "MEGA.JK"],
        "Consumer": ["UNVR.JK", "ICBP.JK", "INDF.JK", "KLBF.JK", "HMSP.JK", "MYOR.JK", "ROTI.JK", "GOOD.JK", "PSKT.JK", "ACES.JK"],
        "Mining": ["ANTM.JK", "TINS.JK", "PTBA.JK", "ADRO.JK", "ITMG.JK", "KDTN.JK", "INDY.JK", "DEWA.JK", "PKRT.JK", "HRUM.JK", "ADMR.JK", "BRMS.JK", "BUMI.JK", "CUAN.JK", "PTRO.JK", "MBMA.JK", "NICL.JK", "RAJA.JK", "TOBA.JK"],
        "Property": ["BSDE.JK", "PWON.JK", "SMRA.JK", "CTRA.JK", "LPKR.JK", "DMAS.JK", "PPRO.JK", "GMTD.JK", "DART.JK"],
        "Automotive": ["ASII.JK", "GJTL.JK", "IMAS.JK", "MAPI.JK", "RALS.JK", "SMSM.JK", "HEXA.JK", "BOLT.JK"],
        "Telecom": ["TLKM.JK", "EXCL.JK", "FREN.JK", "ISAT.JK", "HEAL.JK", "MTEL.JK", "TOWR.JK", "TBIG.JK"],
        "Tech": ["GOTO.JK", "BUKA.JK", "MCAS.JK", "BALI.JK", "DMMX.JK", "EDGE.JK", "MTDL.JK", "MLPT.JK", "TECH.JK", "KIOS.JK"],
        "Healthcare": ["PRDA.JK", "MIKA.JK", "SILO.JK", "HEAL.JK", "ELSA.JK", "KARW.JK", "SOHO.JK", "MEDC.JK", "PGEO.JK"],
        "Chemicals": ["TPIA.JK", "UNVR.JK", "AKPI.JK", "ARGO.JK", "SMGR.JK", "WSKT.JK"],
        "Oil & Gas": ["UNSP.JK", "PTDO.JK", "MITI.JK", "RUIS.JK", "ELSA.JK", "PMAX.JK", "AKRA.JK", "UNTR.JK"],
        "Retail": ["MAPA.JK", "MAPI.JK", "RALS.JK", "HERO.JK", "MAT1.JK", "AMRT.JK", "LPPF.JK", "ERAA.JK"],
        "Infrastructure": ["PTPP.JK", "WIKA.JK", "WEGE.JK", "ADHI.JK", "JMAS.JK", "JSMR.JK", "TOTL.JK", "SSIA.JK", "DGIK.JK", "WTON.JK"],
        "Power & Energy": ["PGAS.JK", "PTUN.JK", "MADE.JK", "KOPI.JK", "PWER.JK"],
        "Metal & Mineral": ["AMMN.JK", "MDKA.JK", "INCO.JK", "NICL.JK"],
        "Shipping & Maritime": ["TPMA.JK", "WINS.JK", "HITS.JK", "BBRM.JK", "SMDR.JK", "TMAS.JK", "SOCI.JK"]
    })


# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

@dataclass
class AppConfig:
    """Main application configuration."""

    # App metadata
    APP_NAME: str = "IHSG Stock Screener"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Real-time Indonesian Stock Market Screener"

    # Session config
    session: SessionConfig = field(default_factory=SessionConfig)

    # Scoring config
    scoring: ScoringConfig = field(default_factory=ScoringConfig)

    # Recommendation config
    recommendation: RecommendationConfig = field(default_factory=RecommendationConfig)

    # Data source config
    data_source: DataSourceConfig = field(default_factory=DataSourceConfig)

    # UI config
    ui: UIConfig = field(default_factory=UIConfig)

    # Watchlist config
    watchlist: WatchlistConfig = field(default_factory=WatchlistConfig)

    # BSJP config
    bsjp: BSJPConfig = field(default_factory=BSJPConfig)

    def get_all_configs(self) -> Dict:
        """Get all configurations as a dictionary."""
        return {
            'session': self.session.__dict__,
            'scoring': self.scoring.__dict__,
            'recommendation': self.recommendation.__dict__,
            'data_source': self.data_source.__dict__,
            'ui': self.ui.__dict__,
            'watchlist': self.watchlist.__dict__
        }


# ============================================================================
# GLOBAL CONFIGURATION INSTANCE
# ============================================================================

config = AppConfig()
