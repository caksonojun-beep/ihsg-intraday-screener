"""
Tests for Visualization Layer Module
=====================================
"""

import pytest
from datetime import datetime, timedelta
from modules.visualization_layer import VisualizationLayer, ChartConfig


class TestVisualizationLayer:
    """Test cases for VisualizationLayer class."""

    @pytest.fixture
    def viz(self):
        """Create a VisualizationLayer instance for testing."""
        return VisualizationLayer(theme="dark")

    def test_initialization(self, viz):
        """Test layer initialization."""
        assert viz is not None
        assert viz.theme == "dark"
        assert viz.config is not None

    def test_dark_theme_setup(self, viz):
        """Test dark theme configuration."""
        assert viz.layout_config['paper_bgcolor'] == '#0E1117'
        assert viz.layout_config['plot_bgcolor'] == '#0E1117'
        assert viz.layout_config['font_color'] == '#FAFAFA'

    def test_light_theme_setup(self):
        """Test light theme configuration."""
        viz = VisualizationLayer(theme="light")
        assert viz.layout_config['paper_bgcolor'] == '#FFFFFF'
        assert viz.layout_config['plot_bgcolor'] == '#F8F9FA'
        assert viz.layout_config['font_color'] == '#1A1A1A'

    def test_get_layout(self, viz):
        """Test layout generation."""
        layout = viz._get_layout("Test Chart", height=400)

        assert 'title' in layout
        assert layout['title']['text'] == "Test Chart"
        assert layout['height'] == 400
        assert 'paper_bgcolor' in layout

    def test_create_candlestick_chart(self, viz):
        """Test candlestick chart creation."""
        timestamps = [datetime.now() + timedelta(hours=i) for i in range(10)]
        opens = [100 + i for i in range(10)]
        highs = [105 + i for i in range(10)]
        lows = [95 + i for i in range(10)]
        closes = [102 + i for i in range(10)]
        volumes = [1000000 + i * 10000 for i in range(10)]

        fig = viz.create_candlestick_chart(
            timestamps=timestamps,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
            ticker="BBCA.JK",
            show_volume=True,
            height=500
        )

        assert fig is not None
        assert len(fig.data) > 0

    def test_create_line_chart(self, viz):
        """Test line chart creation."""
        timestamps = [datetime.now() + timedelta(hours=i) for i in range(10)]
        values = [100 + i * 2 for i in range(10)]

        fig = viz.create_line_chart(
            timestamps=timestamps,
            values=values,
            name="Price",
            show_area=False
        )

        assert fig is not None
        assert len(fig.data) == 1

    def test_create_score_gauge(self, viz):
        """Test score gauge creation."""
        fig = viz.create_score_gauge(
            score=85,
            signal="BUY",
            height=200
        )

        assert fig is not None
        assert len(fig.data) == 1

    def test_create_score_breakdown_chart(self, viz):
        """Test score breakdown chart creation."""
        breakdown = {
            'Volume': 85.0,
            'BO Ratio': 75.0,
            'Price': 90.0,
            'Spread': 80.0,
            'Market Cap': 95.0
        }

        fig = viz.create_score_breakdown_chart(breakdown, height=300)

        assert fig is not None
        assert len(fig.data) == 1

    def test_create_comparison_bar_chart(self, viz):
        """Test comparison bar chart creation."""
        data = {
            'Stock A': 100,
            'Stock B': 75,
            'Stock C': 50
        }

        fig = viz.create_comparison_bar_chart(data, title="Comparison")

        assert fig is not None
        assert len(fig.data) == 1

    def test_create_volume_chart(self, viz):
        """Test volume chart creation."""
        timestamps = [datetime.now() + timedelta(hours=i) for i in range(10)]
        volumes = [1000000 + i * 10000 for i in range(10)]
        avg_volume = 1050000

        fig = viz.create_volume_chart(
            timestamps=timestamps,
            volumes=volumes,
            avg_volume=avg_volume
        )

        assert fig is not None
        assert len(fig.data) == 2  # Bars + average line

    def test_create_price_change_chart(self, viz):
        """Test price change chart creation."""
        data = [
            {'ticker': 'A', 'name': 'Stock A', 'change_pct': 5.0},
            {'ticker': 'B', 'name': 'Stock B', 'change_pct': -2.0},
            {'ticker': 'C', 'name': 'Stock C', 'change_pct': 0.5}
        ]

        fig = viz.create_price_change_chart(data)

        assert fig is not None
        assert len(fig.data) == 1

    def test_create_market_overview_pie(self, viz):
        """Test market overview pie chart creation."""
        fig = viz.create_market_overview_pie(
            gainers=10,
            losers=5,
            unchanged=3
        )

        assert fig is not None
        assert len(fig.data) == 1

    def test_create_strategy_comparison(self, viz):
        """Test strategy comparison chart creation."""
        strategies = [
            {'strategy': 'Aggressive', 'target_pct': 10, 'stop_loss_pct': 2},
            {'strategy': 'Moderate', 'target_pct': 5, 'stop_loss_pct': 3},
            {'strategy': 'Conservative', 'target_pct': 3, 'stop_loss_pct': 2}
        ]

        fig = viz.create_strategy_comparison(strategies)

        assert fig is not None
        assert len(fig.data) == 2  # Target and Stop Loss bars


class TestChartConfig:
    """Test cases for ChartConfig dataclass."""

    def test_default_config(self):
        """Test default chart configuration."""
        config = ChartConfig()

        assert config.template == "plotly_dark"
        assert config.colors is not None
        assert 'up' in config.colors
        assert 'down' in config.colors
        assert 'neutral' in config.colors

    def test_custom_colors(self):
        """Test custom color configuration."""
        config = ChartConfig(
            colors={
                'up': '#00FF00',
                'down': '#FF0000',
                'neutral': '#FFFFFF'
            }
        )

        assert config.colors['up'] == '#00FF00'
        assert config.colors['down'] == '#FF0000'
