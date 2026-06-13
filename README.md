# IHSG Stock Screener

A production-ready Indonesian Stock Market Screener built with Streamlit, featuring real-time data fetching, AI-powered scoring, and comprehensive trading recommendations.

## 📊 Features

### Core Functionality
- **Real-time Data Fetching**: Yahoo Finance integration for live market data
- **Session Detection**: Automatic detection of Indonesian stock market sessions (Pre-Market, Regular, After Hours)
- **AI-Powered Scoring**: Multi-factor scoring engine with weighted components
- **Trading Recommendations**: Entry, target, and stop-loss recommendations with risk analysis
- **Interactive Visualizations**: Plotly-based candlestick charts, gauges, and comparison charts

### Modules
1. **Session Engine**: Market session detection and status
2. **Data Fetcher**: Batch data fetching with caching and retry logic
3. **Scoring Engine**: Comprehensive stock scoring algorithm
4. **Recommendation Engine**: Trading strategy generation
5. **Visualization Layer**: Interactive Plotly charts

## 🏗️ Architecture

```
User -> Streamlit UI -> yFinance -> Scoring Engine -> Recommendation Engine -> Visualization -> UI
```

### Data Flow
1. User opens application
2. Session engine detects market status
3. Data fetcher retrieves stock data from Yahoo Finance
4. Scoring engine calculates comprehensive scores
5. Recommendation engine generates trading strategies
6. Visualization layer renders interactive charts

## 📁 Project Structure

```
ihsg/
├── app.py                    # Main Streamlit application
├── config.py                # Configuration settings
├── requirements.txt        # Python dependencies
├── modules/
│   ├── __init__.py         # Module exports
│   ├── session_engine.py   # Market session detection
│   ├── data_fetcher.py     # Yahoo Finance integration
│   ├── scoring_engine.py  # Stock scoring algorithm
│   ├── recommendation_engine.py  # Trading recommendations
│   └── visualization_layer.py    # Plotly charts
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Pytest configuration
│   ├── test_session_engine.py
│   ├── test_scoring_engine.py
│   ├── test_recommendation_engine.py
│   └── test_visualization_layer.py
├── .streamlit/
│   └── config.toml        # Streamlit configuration
└── pytest.ini              # Pytest configuration
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ihsg
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run app.py
```

### Running Tests

```bash
pytest tests/ -v
```

## 📈 Scoring System

### Score Components
| Component | Weight | Description |
|----------|--------|-------------|
| Volume Spike | 25% | Volume relative to average |
| BO Ratio | 25% | Buy/Order ratio indicator |
| Price Change | 20% | Recent price movement |
| Spread | 15% | Bid-ask spread tightness |
| Market Cap | 15% | Company size factor |

### Signal Thresholds
| Signal | Score Range |
|--------|------------|
| STRONG BUY | 85-100 |
| BUY | 70-84 |
| HOLD | 50-69 |
| SELL | 30-49 |
| STRONG SELL | 0-29 |

## 📋 UI Components

### Sidebar
- Session status display
- Filter settings (min score, volume spike, BO ratio)
- Auto-refresh toggle
- Watchlist selection

### Main Screener Table
- Sortable columns
- Dark theme styling
- Score badges
- Signal indicators

### Detail Page
- Header metrics
- Strategy card with entry/target/stop-loss
- Candlestick chart
- Real-time metrics
- Flow analysis

## ⚙️ Configuration

### Session Hours (WIB)
- Pre-Market: 07:00 - 08:30
- Regular Session: 08:30 - 15:30
- After Hours: 15:30 - 15:50

### Default Watchlist
- Banking: BBCA.JK, BBRI.JK, BMRI.JK, BBNI.JK, BDMN.JK
- Consumer: UNVR.JK, ICBP.JK, INDF.JK, KLBF.JK, HMSP.JK
- Mining: ANTM.JK, TINS.JK, PTBA.JK, ADRO.JK, ITMG.JK
- Property: BSDE.JK, PWON.JK, SMRA.JK, CTRA.JK, LPKR.JK
- Automotive: ASII.JK, GJTL.JK, IMAS.JK
- Telecom: TLKM.JK, EXCL.JK, FREN.JK

## 🔧 Development

### Adding New Tickers
Edit `config.py` and add to `WatchlistConfig.DEFAULT_TICKERS` or `TICKER_GROUPS`.

### Modifying Scoring Weights
Edit `config.py` `ScoringConfig.WEIGHTS` dictionary.

### Adding New Chart Types
Add methods to `modules/visualization_layer.py`.

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📚 Documentation

See the `/docs` directory for detailed specifications:
- `ARCHITECTURE.md` - System architecture
- `DATA_MODEL.md` - Data structures
- `UI_SPEC.md` - User interface specification
- `USER_FLOW.md` - User interaction flow
- `TASK_BREAKDOWN.md` - Development tasks
