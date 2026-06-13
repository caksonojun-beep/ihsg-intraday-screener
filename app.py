"""
IHSG Stock Screener - Main Application
======================================
Streamlit-based Indonesian Stock Market Screener
Real-time screening with scoring and recommendations.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules
from config import config
from modules import (
    SessionEngine,
    DataFetcher,
    ScoringEngine,
    RecommendationEngine,
    VisualizationLayer,
    ScoredStock,
    StockData,
    SignalType,
    BSJPDetector,
    BSJPStock,
    GapType,
    BPJSDetector,
    BPJSStock,
    BPJSSignal
)


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# CUSTOM CSS STYLING
# ============================================================================

def apply_custom_css():
    """Apply custom CSS styling for dark theme and components."""
    st.markdown("""
    <style>
        /* Main background */
        .stApp {
            background-color: #0E1117;
        }

        /* Custom metric cards */
        .metric-card {
            background-color: #1E1E1E;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #00D4AA;
        }

        /* Score badge styles */
        .score-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            text-align: center;
        }

        .score-high {
            background-color: #00D4AA;
            color: #0E1117;
        }

        .score-medium {
            background-color: #FFA500;
            color: #0E1117;
        }

        .score-low {
            background-color: #FF6B6B;
            color: #FFFFFF;
        }

        /* Signal indicator */
        .signal-indicator {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
            text-transform: uppercase;
        }

        .signal-strong-buy {
            background-color: #00D4AA;
            color: #0E1117;
        }

        .signal-buy {
            background-color: #90EE90;
            color: #0E1117;
        }

        .signal-hold {
            background-color: #FFFF00;
            color: #0E1117;
        }

        .signal-sell {
            background-color: #FFA500;
            color: #0E1117;
        }

        .signal-strong-sell {
            background-color: #FF6B6B;
            color: #FFFFFF;
        }

        /* Session status */
        .session-status {
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
        }

        .session-open {
            background-color: #00D4AA33;
            border: 2px solid #00D4AA;
            color: #00D4AA;
        }

        .session-closed {
            background-color: #FF6B6B33;
            border: 2px solid #FF6B6B;
            color: #FF6B6B;
        }

        /* Sidebar styling */
        .css-1d391kg {
            background-color: #1E1E1E;
        }

        /* DataFrame styling */
        .dataframe {
            border: none !important;
        }

        /* Hide default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Custom table styles */
        table {
            border-collapse: collapse;
            width: 100%;
        }

        th {
            background-color: #1E1E1E !important;
            color: #FAFAFA !important;
            padding: 12px !important;
            text-align: left !important;
        }

        td {
            padding: 10px !important;
            border-bottom: 1px solid #2D2D2D !important;
        }

        tr:hover {
            background-color: #2D2D2D !important;
        }

        /* Price change colors */
        .positive {
            color: #00D4AA !important;
        }

        .negative {
            color: #FF6B6B !important;
        }

        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #1E1E1E;
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# INITIALIZE SESSION STATE
# ============================================================================

def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'data_fetcher' not in st.session_state:
        st.session_state.data_fetcher = DataFetcher()

    if 'scoring_engine' not in st.session_state:
        st.session_state.scoring_engine = ScoringEngine(
            weights=config.scoring.weights,
            min_score=config.scoring.MIN_SCORE,
            max_score=config.scoring.MAX_SCORE
        )

    if 'recommendation_engine' not in st.session_state:
        st.session_state.recommendation_engine = RecommendationEngine()

    if 'session_engine' not in st.session_state:
        st.session_state.session_engine = SessionEngine()

    if 'viz_layer' not in st.session_state:
        st.session_state.viz_layer = VisualizationLayer(theme="dark")

    if 'bsjp_detector' not in st.session_state:
        st.session_state.bsjp_detector = BSJPDetector(
            gap_up_threshold=config.bsjp.GAP_UP_THRESHOLD,
            gap_down_threshold=config.bsjp.GAP_DOWN_THRESHOLD,
            closing_volume_spike_min=config.bsjp.CLOSING_VOLUME_SPIKE_MIN,
            closing_price_momentum_min=config.bsjp.CLOSING_PRICE_MOMENTUM_MIN
        )

    if 'bpjs_detector' not in st.session_state:
        st.session_state.bpjs_detector = BPJSDetector(
            min_morning_momentum=1.0,
            min_volume_spike=1.5
        )

    if 'scored_stocks' not in st.session_state:
        st.session_state.scored_stocks = []

    if 'bsjp_stocks' not in st.session_state:
        st.session_state.bsjp_stocks = []

    if 'bpjs_stocks' not in st.session_state:
        st.session_state.bpjs_stocks = []

    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None

    if 'selected_ticker' not in st.session_state:
        st.session_state.selected_ticker = None

    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = config.ui.AUTO_REFRESH_DEFAULT


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@st.cache_data(ttl=300)
def fetch_and_score_stocks(tickers: List[str]) -> Tuple[List[ScoredStock], float]:
    """
    Fetch and score stocks with caching.

    Args:
        tickers: List of stock tickers

    Returns:
        Tuple of (scored stocks list, fetch time)
    """
    fetcher = st.session_state.data_fetcher
    scoring = st.session_state.scoring_engine

    # Fetch batch data
    result = fetcher.fetch_batch(tickers)

    # Convert to scoring format
    stocks_data = []
    for stock in result.stocks:
        stocks_data.append({
            'ticker': stock.ticker,
            'name': stock.name,
            'price': stock.price,
            'change_pct': stock.change_pct,
            'volume_spike': stock.volume_spike,
            'rsi': stock.rsi,
            'macd_signal': stock.macd_signal,
            'spread': stock.spread,
            'market_cap': stock.market_cap
        })

    # Score all stocks
    scored = scoring.score_batch(stocks_data)

    return scored, result.fetch_time


@st.cache_data(ttl=60)
def fetch_candlestick_data(ticker: str, interval: str, period: str):
    """
    Fetch candlestick data with caching.

    Args:
        ticker: Stock ticker
        interval: Chart interval
        period: Data period

    Returns:
        Candlestick data object
    """
    fetcher = st.session_state.data_fetcher
    return fetcher.fetch_candlestick(ticker, interval, period)


def format_currency(value: float) -> str:
    """Format value as Indonesian Rupiah."""
    if value >= 1_000_000_000_000:
        return f"IDR {value/1_000_000_000_000:.2f}T"
    elif value >= 1_000_000_000:
        return f"IDR {value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"IDR {value/1_000_000:.2f}M"
    else:
        return f"IDR {value:,.0f}"


def format_percentage(value: float) -> str:
    """Format value as percentage with sign."""
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def get_signal_class(signal: str) -> str:
    """Get CSS class for signal type."""
    signal_classes = {
        'STRONG BUY': 'signal-strong-buy',
        'BUY': 'signal-buy',
        'HOLD': 'signal-hold',
        'SELL': 'signal-sell',
        'STRONG SELL': 'signal-strong-sell'
    }
    return signal_classes.get(signal, 'signal-hold')


def get_score_class(score: int) -> str:
    """Get CSS class for score range."""
    if score >= 70:
        return 'score-high'
    elif score >= 50:
        return 'score-medium'
    else:
        return 'score-low'


# ============================================================================
# SIDEBAR COMPONENTS
# ============================================================================

def render_sidebar():
    """Render sidebar with filters and session status."""
    with st.sidebar:
        st.markdown("---")
        st.markdown("## 📊 IHSG Screener")
        st.markdown("---")

        # Session Status
        render_session_status()

        st.markdown("---")

        # Filter Settings
        st.markdown("### ⚙️ Filter Settings")

        # Min Score Slider
        min_score = st.slider(
            "📊 Minimum Score",
            min_value=0,
            max_value=100,
            value=50,
            help="Filter stocks by minimum score threshold"
        )
        st.caption("""
        **Score Range:** 0-100
        - 85-100: STRONG BUY 🟢
        - 70-84: BUY 🟢
        - 50-69: HOLD 🟡
        - 30-49: SELL 🟠
        - 0-29: STRONG SELL 🔴
        """)

        # Min Volume Spike Slider
        min_volume_spike = st.slider(
            "📈 Min Volume Spike",
            min_value=0.0,
            max_value=5.0,
            value=1.0,
            step=0.1,
            help="Minimum volume spike ratio (x average)"
        )
        st.caption("""
        **Volume Spike:** Volume sekarang vs rata-rata
        - 3.0x+ : Exceptional (mendadak bullish)
        - 2.0x+ : Strong (volume tinggi)
        - 1.5x+ : Moderate
        - 1.0x : Normal
        """)

        # Min RSI Slider
        min_rsi = st.slider(
            "📊 Min RSI",
            min_value=0,
            max_value=100,
            value=50,
            help="Minimum RSI value for momentum"
        )
        st.caption("""
        **RSI (Relative Strength Index):** 0-100

        | RSI | Kondisi | Sinyal |
        |-----|---------|--------|
        | 70+ | Overbought | 🟢 Strong momentum |
        | 60-70 | Bullish zone | 🟢 Ideal buy |
        | 50-60 | Building momentum | 🟡 Mulai naik |
        | 40-50 | Neutral | 🟡 Wait & see |
        | 30-40 | Bearish zone | 🟠 Hati-hati |
        | < 30 | Oversold | 🔴 Bisa reversal |

        **MACD:** Histogram positif = bullish, negatif = bearish
        """)

        st.markdown("---")

        # Auto Refresh Settings
        st.markdown("### 🔄 Auto Refresh")

        auto_refresh = st.checkbox(
            "Enable Auto Refresh",
            value=st.session_state.auto_refresh,
            help="Automatically refresh data"
        )
        st.session_state.auto_refresh = auto_refresh

        if auto_refresh:
            refresh_interval = st.selectbox(
                "Refresh Interval",
                options=[30, 60, 120, 300],
                index=1,
                format_func=lambda x: f"{x} seconds"
            )
        else:
            refresh_interval = 60

        st.markdown("---")

        # Watchlist Selection
        st.markdown("### 📋 Watchlist")

        watchlist_groups = list(config.watchlist.TICKER_GROUPS.keys())
        selected_groups = st.multiselect(
            "Select Groups",
            options=watchlist_groups,
            default=watchlist_groups,
            help="Select stock groups to include"
        )

        # Get selected tickers
        selected_tickers = []
        for group in selected_groups:
            selected_tickers.extend(config.watchlist.TICKER_GROUPS[group])

        # Add custom tickers
        custom_tickers = st.text_input(
            "Custom Tickers",
            value="",
            placeholder="e.g., BBCA.JK, BBRI.JK",
            help="Add custom tickers (comma separated)"
        )

        if custom_tickers:
            custom_list = [t.strip().upper() for t in custom_tickers.split(',')]
            selected_tickers.extend(custom_list)

        # Remove duplicates
        selected_tickers = list(set(selected_tickers))

        st.markdown("---")

        # Data Stats
        if st.session_state.scored_stocks:
            st.markdown("### 📈 Data Stats")
            st.caption(f"Stocks loaded: {len(st.session_state.scored_stocks)}")
            if st.session_state.last_refresh:
                st.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

        return {
            'min_score': min_score,
            'min_volume_spike': min_volume_spike,
            'min_rsi': min_rsi,
            'auto_refresh': auto_refresh,
            'refresh_interval': refresh_interval,
            'selected_tickers': selected_tickers
        }


def render_session_status():
    """Render market session status display."""
    session_engine = st.session_state.session_engine
    session_info = session_engine.get_session_info()

    status_class = "session-open" if session_info.is_trading_active else "session-closed"

    st.markdown(f"""
    <div class="session-status {status_class}">
        <div style="font-size: 14px;">{session_info.status_display}</div>
        <div style="font-size: 12px; margin-top: 5px;">{session_info.session_message}</div>
        <div style="font-size: 11px; margin-top: 5px; opacity: 0.8;">
            Next: {session_engine.format_time_remaining(session_info.time_until_change) if session_info.time_until_change else 'N/A'}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# MAIN SCREENER TABLE
# ============================================================================

def render_screener_table(stocks: List[ScoredStock], filters: Dict):
    """
    Render the main stock screener table.

    Args:
        stocks: List of scored stocks
        filters: Filter settings dictionary
    """
    if not stocks:
        st.warning("No stocks to display. Please select tickers and refresh data.")
        return

    # Apply filters
    filtered_stocks = [
        s for s in stocks
        if s.score >= filters['min_score']
        and s.volume_spike >= filters['min_volume_spike']
    ]

    if not filtered_stocks:
        st.warning("No stocks match the selected filters.")
        return

    # Create DataFrame
    df = pd.DataFrame([
        {
            'Ticker': s.ticker,
            'Name': s.name[:30] + '...' if len(s.name) > 30 else s.name,
            'Price': f"IDR {s.price:,.0f}",
            'Change %': s.change_pct,
            'Volume Spike': f"{s.volume_spike:.2f}x",
            'Spread %': f"{s.spread:.2f}",
            'Market Cap': format_currency(s.market_cap),
            'Score': s.score,
            'Signal': s.signal.value
        }
        for s in filtered_stocks
    ])

    # Add CSS classes for styling
    st.markdown("""
    <style>
        .stock-row {
            cursor: pointer;
        }
        .stock-row:hover {
            background-color: #2D2D2D;
        }
    </style>
    """, unsafe_allow_html=True)

    # Display table with formatting
    st.dataframe(
        df,
        column_config={
            "Ticker": st.column_config.TextColumn(
                "Ticker",
                width="medium",
            ),
            "Name": st.column_config.TextColumn(
                "Name",
                width="large",
            ),
            "Price": st.column_config.TextColumn(
                "Price",
                width="medium",
            ),
            "Change %": st.column_config.NumberColumn(
                "Change %",
                format="%.2f",
                width="small",
            ),
            "Volume Spike": st.column_config.TextColumn(
                "Volume Spike",
                width="small",
            ),
            "Spread %": st.column_config.TextColumn(
                "Spread %",
                width="small",
            ),
            "Market Cap": st.column_config.TextColumn(
                "Market Cap",
                width="medium",
            ),
            "Score": st.column_config.NumberColumn(
                "Score",
                format="%d",
                width="small",
            ),
            "Signal": st.column_config.TextColumn(
                "Signal",
                width="medium",
            ),
        },
        hide_index=True,
        use_container_width=True,
        height=600
    )

    # Store filtered stocks for selection
    st.session_state.filtered_stocks = filtered_stocks


def render_stock_selection(stocks: List[ScoredStock]):
    """
    Render stock selection interface.

    Args:
        stocks: List of scored stocks
    """
    if not stocks:
        return

    st.markdown("### 🔍 Quick Stock Search")
    st.markdown("*Pilih saham untuk melihat detail analysis*")

    # Create selection dropdown with names
    ticker_options = {s.ticker: f"{s.ticker} - {s.name[:20]}..." for s in stocks}

    col1, col2 = st.columns([3, 1])
    with col1:
        selected = st.selectbox(
            "📌 Pilih Saham:",
            options=["-- Pilih Saham --"] + list(ticker_options.keys()),
            format_func=lambda x: ticker_options.get(x, x),
            key="stock_selector"
        )
    with col2:
        st.markdown("")  # Spacing
        if selected != "-- Pilih Saham --":
            if st.button("📊 Lihat Detail", use_container_width=True, type="primary"):
                st.session_state.selected_ticker = selected

    # Show quick info if stock selected from dropdown
    if selected != "-- Pilih Saham --":
        for s in stocks:
            if s.ticker == selected:
                st.markdown(f"""
                <div style="background-color:#1E1E1E; padding:10px; border-radius:8px; margin:10px 0;">
                    <b>{s.ticker}</b> | Price: IDR {s.price:,.0f} |
                    Change: <span style="color:{'#00D4AA' if s.change_pct >= 0 else '#FF6B6B'};">{s.change_pct:+.2f}%</span> |
                    Score: <b>{s.score}</b> | Signal: <b>{s.signal.value}</b>
                </div>
                """, unsafe_allow_html=True)
                break


# ============================================================================
# DETAIL PAGE
# ============================================================================

def render_detail_page(ticker: str):
    """
    Render detailed view for a single stock.

    Args:
        ticker: Stock ticker symbol
    """
    # Find the stock in session state
    stock = None
    for s in st.session_state.scored_stocks:
        if s.ticker == ticker:
            stock = s
            break

    if not stock:
        st.error(f"Stock {ticker} not found in loaded data.")
        return

    # Header
    st.markdown(f"## 📊 {stock.ticker} - {stock.name}")
    st.markdown("---")

    # Header Metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Price",
            f"IDR {stock.price:,.0f}",
            f"{stock.change_pct:+.2f}%"
        )

    with col2:
        st.metric("Score", stock.score)

    with col3:
        st.metric("Signal", stock.signal.value)

    with col4:
        st.metric("Volume Spike", f"{stock.volume_spike:.2f}x")

    with col5:
        st.metric("BO Ratio", f"{stock.bo_ratio:.2f}")

    st.markdown("---")

    # Strategy Card
    render_strategy_card(stock)

    st.markdown("---")

    # Chart Section
    render_chart_section(ticker)

    st.markdown("---")

    # Real-time Metrics
    render_metrics_section(stock)

    st.markdown("---")

    # Flow Analysis
    render_flow_analysis(stock)


def render_strategy_card(stock: ScoredStock):
    """Render strategy recommendation card."""
    recommendation = st.session_state.recommendation_engine.generate_recommendation(
        ticker=stock.ticker,
        name=stock.name,
        price=stock.price,
        change_pct=stock.change_pct,
        volume_spike=stock.volume_spike,
        spread=stock.spread,
        market_cap=stock.market_cap,
        score=stock.score,
        signal=stock.signal.value
    )

    st.markdown("### 🎯 Trading Strategy")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Entry & Targets")
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 12px; color: #888;">Entry Price</div>
            <div style="font-size: 24px; font-weight: bold;">IDR {recommendation.price_levels.entry_price:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #00D4AA;">
            <div style="font-size: 12px; color: #00D4AA;">Target Price</div>
            <div style="font-size: 20px; font-weight: bold; color: #00D4AA;">IDR {recommendation.price_levels.target_price:,.0f}</div>
            <div style="font-size: 12px; color: #00D4AA;">+{recommendation.price_levels.target_pct}%</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #FF6B6B;">
            <div style="font-size: 12px; color: #FF6B6B;">Stop Loss</div>
            <div style="font-size: 20px; font-weight: bold; color: #FF6B6B;">IDR {recommendation.price_levels.stop_loss_price:,.0f}</div>
            <div style="font-size: 12px; color: #FF6B6B;">-{recommendation.price_levels.stop_loss_pct}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### Risk/Reward")
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #1E88E5;">
            <div style="font-size: 12px; color: #888;">Risk/Reward Ratio</div>
            <div style="font-size: 32px; font-weight: bold; color: #1E88E5;">{recommendation.price_levels.risk_reward_ratio:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 12px; color: #888;">Max Loss</div>
            <div style="font-size: 18px; font-weight: bold;">IDR {recommendation.metrics.max_loss_amount:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 12px; color: #888;">Max Profit</div>
            <div style="font-size: 18px; font-weight: bold;">IDR {recommendation.metrics.max_profit_amount:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("#### Strategy Details")
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 12px; color: #888;">Strategy Type</div>
            <div style="font-size: 18px; font-weight: bold;">{recommendation.strategy.value}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 12px; color: #888;">Risk Level</div>
            <div style="font-size: 18px; font-weight: bold;">{recommendation.metrics.risk_level.value}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 12px; color: #888;">Holding Period</div>
            <div style="font-size: 18px; font-weight: bold;">{recommendation.metrics.holding_period}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 12px; color: #888;">Position Size</div>
            <div style="font-size: 18px; font-weight: bold;">{recommendation.metrics.position_size_recommendation}</div>
        </div>
        """, unsafe_allow_html=True)

    # Rationale
    st.markdown("#### 💡 Trading Rationale")
    st.info(recommendation.rationale)


def render_chart_section(ticker: str):
    """Render candlestick chart section."""
    st.markdown("### 📈 Price Chart")

    col1, col2 = st.columns([3, 1])

    with col2:
        interval = st.selectbox(
            "Interval",
            options=["1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1wk"],
            index=7,
            key="chart_interval"
        )

        period = st.selectbox(
            "Period",
            options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"],
            index=2,
            key="chart_period"
        )

    with col1:
        # Fetch candlestick data
        candle_data = fetch_candlestick_data(ticker, interval, period)

        if candle_data.timestamp:
            # Create candlestick chart
            fig = st.session_state.viz_layer.create_candlestick_chart(
                timestamps=candle_data.timestamp,
                opens=candle_data.open,
                highs=candle_data.high,
                lows=candle_data.low,
                closes=candle_data.close,
                volumes=candle_data.volume,
                ticker=ticker,
                show_volume=True,
                height=450
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No chart data available.")


def render_metrics_section(stock: ScoredStock):
    """Render real-time metrics section."""
    st.markdown("### 📊 Real-time Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 12px; color: #888;">Volume Spike</div>
            <div style="font-size: 24px; font-weight: bold;">{:.2f}x</div>
            <div style="font-size: 11px; color: #00D4AA;">vs Average</div>
        </div>
        """.format(stock.volume_spike), unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 12px; color: #888;">Bid-Ask Spread</div>
            <div style="font-size: 24px; font-weight: bold;">{:.2f}%</div>
            <div style="font-size: 11px; color: #888;">Liquidity</div>
        </div>
        """.format(stock.spread), unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 12px; color: #888;">Market Cap</div>
            <div style="font-size: 20px; font-weight: bold;">{}</div>
        </div>
        """.format(format_currency(stock.market_cap)), unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 12px; color: #888;">Score Breakdown</div>
            <div style="font-size: 14px; font-weight: bold;">Volume: {:.0f}</div>
            <div style="font-size: 14px; font-weight: bold;">BO Ratio: {:.0f}</div>
            <div style="font-size: 14px; font-weight: bold;">Price: {:.0f}</div>
        </div>
        """.format(
            stock.score_breakdown.volume_score,
            stock.score_breakdown.bo_ratio_score,
            stock.score_breakdown.price_change_score
        ), unsafe_allow_html=True)


def render_flow_analysis(stock: ScoredStock):
    """Render flow analysis section."""
    st.markdown("### 🔄 Flow Analysis")

    col1, col2 = st.columns(2)

    with col1:
        # Score breakdown chart
        breakdown = {
            'Volume': stock.score_breakdown.volume_score,
            'BO Ratio': stock.score_breakdown.bo_ratio_score,
            'Price': stock.score_breakdown.price_change_score,
            'Spread': stock.score_breakdown.spread_score,
            'Market Cap': stock.score_breakdown.market_cap_score
        }

        fig = st.session_state.viz_layer.create_score_breakdown_chart(breakdown, height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Score gauge
        fig = st.session_state.viz_layer.create_score_gauge(
            score=stock.score,
            signal=stock.signal.value,
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# MARKET OVERVIEW
# ============================================================================

def render_market_overview():
    """Render market overview section."""
    if not st.session_state.scored_stocks:
        return

    st.markdown("### 📊 Market Overview")

    stocks = st.session_state.scored_stocks

    # Calculate statistics
    gainers = sum(1 for s in stocks if s.change_pct > 0)
    losers = sum(1 for s in stocks if s.change_pct < 0)
    unchanged = len(stocks) - gainers - losers

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Stocks", len(stocks))

    with col2:
        st.metric("Gainers", gainers, delta=gainers)

    with col3:
        st.metric("Losers", losers, delta=-losers)

    with col4:
        avg_change = sum(s.change_pct for s in stocks) / len(stocks)
        st.metric("Avg Change", f"{avg_change:+.2f}%")

    # Market pie chart
    col1, col2 = st.columns([1, 2])

    with col1:
        fig = st.session_state.viz_layer.create_market_overview_pie(
            gainers=gainers,
            losers=losers,
            unchanged=unchanged,
            height=250
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Top movers
        top_gainers = sorted(stocks, key=lambda x: x.change_pct, reverse=True)[:5]
        top_losers = sorted(stocks, key=lambda x: x.change_pct)[:5]

        st.markdown("#### Top Gainers")
        for s in top_gainers:
            st.markdown(f"- **{s.ticker}**: {s.change_pct:+.2f}%")

        st.markdown("#### Top Losers")
        for s in top_losers:
            st.markdown(f"- **{s.ticker}**: {s.change_pct:+.2f}%")


# ============================================================================
# BSJP DETECTOR SECTION
# ============================================================================

def render_bsjp_section():
    """Render BSJP (Beli Sore Jual Pagi) detector section."""
    if not st.session_state.scored_stocks:
        return

    st.markdown("---")
    st.markdown("### 🌙 BSJP Detector")
    st.markdown("*Beli Sore Jual Pagi - Overnight Trading Strategy*")

    # Analyze stocks for BSJP
    if st.session_state.bsjp_stocks:
        bsjp_stocks = st.session_state.bsjp_stocks
    else:
        # Analyze scored stocks for BSJP
        stocks_data = [{
            'ticker': s.ticker,
            'name': s.name,
            'price': s.price,
            'change_pct': s.change_pct,
            'volume_spike': s.volume_spike
        } for s in st.session_state.scored_stocks]

        bsjp_stocks = st.session_state.bsjp_detector.analyze_batch(stocks_data)
        st.session_state.bsjp_stocks = bsjp_stocks

    # Filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        min_score = st.slider(
            "🎯 Min BSJP Score",
            min_value=0,
            max_value=100,
            value=60,
            help="Minimum BSJP score for filtering"
        )
        st.caption("""
        **BSJP Score:** 0-100

        | Score | Rekomendasi |
        |-------|-------------|
        | 75+ | ⭐ STRONG BSJP |
        | 60-74 | ✅ BSJP |
        | 45-59 | 👀 WATCH |
        | < 45 | ❌ AVOID |
        """)

    with col2:
        min_change = st.slider(
            "📈 Min Price Change %",
            min_value=0.0,
            max_value=10.0,
            value=1.0,
            step=0.5,
            help="Minimum price change percentage"
        )
        st.caption("""
        **Price Change:** Perubahan harga hari ini

        - 3%+ : Exceptional momentum
        - 2%+ : Strong momentum
        - 1%+ : Moderate momentum
        - < 1% : Weak
        """)

    with col3:
        filter_type = st.selectbox(
            "🔍 Filter by Gap",
            options=["All", "GAP UP", "NO GAP"],
            help="Filter by gap type"
        )
        st.caption("""
        **Gap Type:**

        - GAP UP: Potensi lonjakan besok
        - NO GAP: Stabil, tanpa gap
        - GAP DOWN: Hati-hati, bisa turun
        """)

    # Filter stocks
    filtered = st.session_state.bsjp_detector.filter_bsjp_stocks(
        bsjp_stocks,
        min_score=min_score,
        min_change=min_change
    )

    if filter_type != "All":
        gap_type = GapType.GAP_UP if filter_type == "GAP UP" else GapType.NO_GAP
        filtered = [s for s in filtered if s.gap_type == gap_type]

    if not filtered:
        st.info("Tidak ada saham yang match dengan filter BSJP.")
        return

    # Display BSJP table
    df = pd.DataFrame([
        {
            'Ticker': s.ticker,
            'Change %': s.change_pct,
            'Volume': f"{s.volume_spike:.2f}x",
            'BSJP Score': s.bsjp_score,
            'Gap': s.gap_type.value,
            'Recommendation': s.recommendation
        }
        for s in filtered
    ])

    st.dataframe(
        df,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="medium"),
            "Change %": st.column_config.NumberColumn("Change %", format="%.2f", width="small"),
            "Volume": st.column_config.TextColumn("Volume", width="small"),
            "BSJP Score": st.column_config.NumberColumn("BSJP Score", format="%d", width="small"),
            "Gap": st.column_config.TextColumn("Gap", width="small"),
            "Recommendation": st.column_config.TextColumn("Recommendation", width="medium"),
        },
        hide_index=True,
        use_container_width=True,
        height=400
    )

    # Top BSJP picks
    st.markdown("#### 🎯 Top BSJP Picks")

    top_bsjp = st.session_state.bsjp_detector.get_top_bsjp_picks(filtered, n=5)

    for i, stock in enumerate(top_bsjp, 1):
        emoji = "⭐" if stock.bsjp_score >= 75 else "✅" if stock.bsjp_score >= 60 else "👀"
        st.markdown(f"""
        **{i}. {stock.ticker}** {emoji}
        - Price: IDR {stock.price:,.0f} | Change: {stock.change_pct:+.2f}%
        - BSJP Score: {stock.bsjp_score} | Gap: {stock.gap_type.value}
        - Recommendation: {stock.recommendation}
        """)

    # BSJP Strategy Info
    with st.expander("📖 BSJP Strategy Guide"):
        st.markdown("""
        **BSJP = Beli Sore Jual Pagi (Overnight Trading)**

        | Window | Waktu | Aksi |
        |--------|-------|------|
        | Buy | 14:30 - 15:50 | Beli di closing session |
        | Sell | 08:30 - 09:30 | Jual di open/pre-market |

        **Score Components:**
        - Closing Momentum (30%): Harga naik di closing
        - Closing Volume (25%): Volume spike di sore hari
        - Gap Potential (20%): Potensi gap up next day
        - After Hours (15%): Pergerakan after hours
        - Pre-Market (10%): Indikasi pre-market

        **Tips:**
        - Cari stocks dengan BSJP Score ≥ 60
        - Gap UP mengindikasikan potensi lonjakan besok
        - Cut loss bila gap down > 2%
        """)


# ============================================================================
# BPJS DETECTOR SECTION
# ============================================================================

def render_bpjs_section():
    """Render BPJS (Beli Pagi Jual Sore) detector section."""
    if not st.session_state.scored_stocks:
        return

    st.markdown("---")
    st.markdown("### ☀️ BPJS Detector")
    st.markdown("*Beli Pagi Jual Sore - Day Trading Strategy*")

    # Analyze stocks for BPJS
    if st.session_state.bpjs_stocks:
        bpjs_stocks = st.session_state.bpjs_stocks
    else:
        # Analyze scored stocks for BPJS
        stocks_data = [{
            'ticker': s.ticker,
            'name': s.name,
            'price': s.price,
            'change_pct': s.change_pct,
            'volume_spike': s.volume_spike
        } for s in st.session_state.scored_stocks]

        bpjs_stocks = st.session_state.bpjs_detector.analyze_batch(stocks_data)
        st.session_state.bpjs_stocks = bpjs_stocks

    # Filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        min_score = st.slider(
            "🎯 Min BPJS Score",
            min_value=0,
            max_value=100,
            value=60,
            help="Minimum BPJS score for filtering"
        )
        st.caption("""
        **BPJS Score:** 0-100

        | Score | Rekomendasi |
        |-------|-------------|
        | 75+ | ⭐ STRONG BPJS |
        | 60-74 | ✅ BPJS |
        | 45-59 | 👀 WATCH |
        | < 45 | ❌ AVOID |
        """)

    with col2:
        min_change = st.slider(
            "📈 Min Price Change %",
            min_value=0.0,
            max_value=10.0,
            value=0.5,
            step=0.5,
            help="Minimum price change percentage"
        )
        st.caption("""
        **Price Change:** Perubahan harga hari ini

        - 3%+ : Exceptional momentum
        - 2%+ : Strong momentum
        - 1%+ : Moderate momentum
        - < 1% : Weak
        """)

    with col3:
        signal_filter = st.selectbox(
            "🔍 Filter by Signal",
            options=["All", "STRONG BPJS", "BPJS"],
            help="Filter by signal type"
        )
        st.caption("""
        **Signal Type:**

        - STRONG BPJS: Siap untuk day trade
        - BPJS: Bisa day trade
        - WATCH: Perlu observasi lebih lanjut
        """)

    # Filter stocks
    filtered = st.session_state.bpjs_detector.filter_bpjs_stocks(
        bpjs_stocks,
        min_score=min_score,
        min_change=min_change
    )

    if signal_filter != "All":
        signal_type = BPJSSignal.STRONG_BPJS if signal_filter == "STRONG BPJS" else BPJSSignal.BPJS
        filtered = [s for s in filtered if s.signal == signal_type]

    if not filtered:
        st.info("Tidak ada saham yang match dengan filter BPJS.")
        return

    # Display BPJS table
    df = pd.DataFrame([
        {
            'Ticker': s.ticker,
            'Change %': s.change_pct,
            'Volume': f"{s.volume_spike:.2f}x",
            'Score': s.bpjs_score,
            'Entry': s.best_entry_window,
            'Exit': s.best_exit_window,
            'Target': f"+{s.target_profit}%",
            'Stop': f"-{s.stop_loss}%",
            'Recommendation': s.recommendation
        }
        for s in filtered
    ])

    st.dataframe(
        df,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="medium"),
            "Change %": st.column_config.NumberColumn("Change %", format="%.2f", width="small"),
            "Volume": st.column_config.TextColumn("Volume", width="small"),
            "Score": st.column_config.NumberColumn("Score", format="%d", width="small"),
            "Entry": st.column_config.TextColumn("Entry Window", width="medium"),
            "Exit": st.column_config.TextColumn("Exit Window", width="medium"),
            "Target": st.column_config.TextColumn("Target", width="small"),
            "Stop": st.column_config.TextColumn("Stop Loss", width="small"),
            "Recommendation": st.column_config.TextColumn("Recommendation", width="medium"),
        },
        hide_index=True,
        use_container_width=True,
        height=400
    )

    # Top BPJS picks
    st.markdown("#### 🎯 Top BPJS Picks")

    top_bpjs = st.session_state.bpjs_detector.get_top_bpjs_picks(filtered, n=5)

    for i, stock in enumerate(top_bpjs, 1):
        emoji = "⭐" if stock.bpjs_score >= 75 else "✅" if stock.bpjs_score >= 60 else "👀"
        st.markdown(f"""
        **{i}. {stock.ticker}** {emoji}
        - Price: IDR {stock.price:,.0f} | Change: {stock.change_pct:+.2f}%
        - Score: {stock.bpjs_score} | Signal: {stock.signal.value}
        - Entry: {stock.best_entry_window}
        - Exit: {stock.best_exit_window}
        - Target: +{stock.target_profit}% | Stop: -{stock.stop_loss}%
        """)

    # BPJS Strategy Info
    with st.expander("📖 BPJS Strategy Guide"):
        st.markdown("""
        **BPJS = Beli Pagi Jual Sore (Day Trading)**

        | Window | Waktu | Aksi |
        |--------|-------|------|
        | Buy | 08:30 - 10:00 | Beli di morning session |
        | Sell | 14:00 - 15:30 | Jual sebelum close |

        **Score Components:**
        - Morning Momentum (30%): Harga naik di pagi
        - Morning Volume (25%): Volume spike di pagi
        - BPJS Volatility (20%): Range harga harian
        - Pre-Closing (15%): Momentum sebelum closing
        - Gap Open (10%): Gap open di pagi

        **Entry Windows:**
        - 08:30-09:00: Gap Up - masuk langsung
        - 09:00-09:30: Wait Pullback - tunggu pullback dulu
        - 09:30-10:00: Confirm Trend - konfirmasi trend dulu

        **Tips:**
        - Target 1-3% per trade
        - Stoploss 0.5-1%
        - Jangan hold overnight!
        - Cut loss cepat kalo salah arah
        """)


# ============================================================================
# COMPARISON VIEW SECTION
# ============================================================================

def render_comparison_view():
    """Render stock comparison view with split panels."""
    if not st.session_state.get('show_comparison', False):
        return

    if not st.session_state.compare_tickers or len(st.session_state.compare_tickers) < 2:
        st.info("Pilih minimal 2 saham untuk compare")
        return

    st.markdown("---")
    st.markdown("### 📊 Stock Comparison View")
    st.markdown("*Bandingkan saham side-by-side*")

    # Close button
    if st.button("❌ Close Comparison"):
        st.session_state.show_comparison = False
        st.rerun()

    # Fetch data for comparison
    tickers = st.session_state.compare_tickers
    fetcher = st.session_state.data_fetcher

    # Create columns based on number of stocks (max 4)
    num_cols = min(len(tickers), 4)
    cols = st.columns(num_cols)

    comparison_data = []

    for i, ticker in enumerate(tickers):
        with cols[i]:
            try:
                stock_data = fetcher.fetch_single_stock(ticker)
                if stock_data.price > 0:
                    comparison_data.append({
                        'ticker': ticker,
                        'name': stock_data.name,
                        'price': stock_data.price,
                        'change_pct': stock_data.change_pct,
                        'volume_spike': stock_data.volume_spike,
                        'spread': stock_data.spread,
                        'market_cap': stock_data.market_cap
                    })
            except Exception:
                continue

    if not comparison_data:
        st.error("Gagal fetch data untuk comparison")
        return

    # Display each stock in a column
    for data in comparison_data:
        with st.container():
            st.markdown(f"""
            <div style="
                background-color: #1E1E1E;
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
                border-left: 4px solid #00D4AA;
            ">
                <h3 style="margin: 0; color: #00D4AA;">{data['ticker']}</h3>
                <p style="margin: 5px 0; color: #888;">{data['name'][:25]}...</p>
                <h2 style="margin: 10px 0;">IDR {data['price']:,.0f}</h2>
                <p style="margin: 5px 0; font-size: 18px; color: {'#00D4AA' if data['change_pct'] >= 0 else '#FF6B6B'};">
                    {data['change_pct']:+.2f}%
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**Metrics:**")
            st.markdown(f"- Volume Spike: **{data['volume_spike']:.2f}x**")
            st.markdown(f"- Spread: **{data['spread']:.2f}%**")
            st.markdown(f"- Market Cap: **{format_currency(data['market_cap'])}**")

            # Mini chart placeholder
            st.markdown("**Chart:**")
            st.info("Klik ticker di atas untuk lihat chart detail")

            st.markdown("---")

    # Summary comparison table
    st.markdown("#### 📋 Summary Comparison")

    summary_df = pd.DataFrame(comparison_data)
    summary_df['Change %'] = summary_df['change_pct'].apply(lambda x: f"{x:+.2f}%")
    summary_df['Volume'] = summary_df['volume_spike'].apply(lambda x: f"{x:.2f}x")
    summary_df['Spread'] = summary_df['spread'].apply(lambda x: f"{x:.2f}%")
    summary_df['Market Cap'] = summary_df['market_cap'].apply(lambda x: format_currency(x))
    summary_df['Price'] = summary_df['price'].apply(lambda x: f"IDR {x:,.0f}")

    st.dataframe(
        summary_df[['ticker', 'name', 'Price', 'Change %', 'Volume', 'Spread', 'Market Cap']],
        hide_index=True,
        use_container_width=True
    )


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    # Apply custom styling
    apply_custom_css()

    # Initialize session state
    init_session_state()

    # Render sidebar and get filters
    filters = render_sidebar()

    # Main content
    st.markdown("# 📈 IHSG Stock Screener")
    st.markdown("Real-time Indonesian Stock Market Screener with AI-powered scoring")

    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True, type="primary"):
            with st.spinner("Fetching and scoring stocks..."):
                try:
                    scored, fetch_time = fetch_and_score_stocks(filters['selected_tickers'])
                    st.session_state.scored_stocks = scored
                    st.session_state.bsjp_stocks = []  # Clear BSJP cache
                    st.session_state.bpjs_stocks = []  # Clear BPJS cache
                    st.session_state.last_refresh = datetime.now()
                    st.success(f"Loaded {len(scored)} stocks in {fetch_time:.2f}s")
                except Exception as e:
                    st.error(f"Error fetching data: {str(e)}")

    st.markdown("---")

    # Auto refresh
    if filters['auto_refresh'] and st.session_state.last_refresh:
        time_since_refresh = (datetime.now() - st.session_state.last_refresh).seconds
        if time_since_refresh >= filters['refresh_interval']:
            st.rerun()

    # Market Overview
    render_market_overview()

    # Comparison View
    render_comparison_view()

    # BSJP Detector
    render_bsjp_section()

    # Intraday Detector
    render_bpjs_section()

    st.markdown("---")

    # Main Screener Table
    st.markdown("### 📋 Stock Screener")

    if st.session_state.scored_stocks:
        render_screener_table(st.session_state.scored_stocks, filters)
    else:
        st.info("Click 'Refresh Data' to load stock data.")

    st.markdown("---")

    # Stock Detail View
    if st.session_state.scored_stocks:
        # Always show stock selector
        render_stock_selection(st.session_state.scored_stocks)

        # Show detail if ticker selected
        if st.session_state.selected_ticker:
            render_detail_page(st.session_state.selected_ticker)

            # Back button
            if st.button("⬅️ Kembali ke List"):
                st.session_state.selected_ticker = None
                st.rerun()
    else:
        st.info("👆 Klik 'Refresh Data' di atas untuk load saham terlebih dahulu.")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
