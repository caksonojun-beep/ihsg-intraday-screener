"""
IHSG Stock Screener - Visualization Layer Module
=================================================
Provides all chart visualizations using Plotly.
Includes candlestick charts, score gauges, and metrics displays.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px


@dataclass
class ChartConfig:
    """Configuration for chart styling."""
    template: str = "plotly_dark"
    colors: Dict[str, str] = None

    def __post_init__(self):
        if self.colors is None:
            self.colors = {
                'up': '#00D4AA',        # Green for gains
                'down': '#FF6B6B',      # Red for losses
                'neutral': '#888888',   # Gray for unchanged
                'primary': '#1E88E5',   # Blue primary
                'secondary': '#00D4AA', # Teal secondary
                'accent': '#FF6B6B',    # Coral accent
                'background': '#0E1117', # Dark background
                'grid': '#2D2D2D'        # Grid lines
            }


class VisualizationLayer:
    """
    Visualization Layer for creating interactive charts.

    Chart Types:
    - Candlestick Chart
    - Volume Bar Chart
    - Score Gauge
    - Price Line Chart
    - Comparison Chart
    - Metrics Cards
    """

    def __init__(self, theme: str = "dark"):
        """
        Initialize the Visualization Layer.

        Args:
            theme: Chart theme ('dark' or 'light')
        """
        self.theme = theme
        self.config = ChartConfig()

        if theme == "dark":
            self._setup_dark_theme()
        else:
            self._setup_light_theme()

    def _setup_dark_theme(self) -> None:
        """Configure dark theme settings."""
        self.layout_config = {
            'paper_bgcolor': '#0E1117',
            'plot_bgcolor': '#0E1117',
            'font_color': '#FAFAFA',
            'gridcolor': '#2D2D2D',
            'title_font_size': 16,
            'axis_font_size': 12
        }

    def _setup_light_theme(self) -> None:
        """Configure light theme settings."""
        self.layout_config = {
            'paper_bgcolor': '#FFFFFF',
            'plot_bgcolor': '#F8F9FA',
            'font_color': '#1A1A1A',
            'gridcolor': '#E0E0E0',
            'title_font_size': 16,
            'axis_font_size': 12
        }

    @staticmethod
    def _hex_to_rgba(hex_color: str, alpha: float = 0.3) -> str:
        """
        Convert hex color to rgba format for Plotly compatibility.

        Args:
            hex_color: Hex color string (e.g., '#1E88E5')
            alpha: Alpha value (0.0 to 1.0)

        Returns:
            RGBA string (e.g., 'rgba(30,136,229,0.3)')
        """
        # Remove # if present
        hex_color = hex_color.lstrip('#')

        # Parse RGB values
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        return f'rgba({r},{g},{b},{alpha})'

    def _get_layout(self, title: str, height: int = 400) -> dict:
        """
        Get base layout configuration.

        Args:
            title: Chart title
            height: Chart height in pixels

        Returns:
            Layout dictionary
        """
        return {
            'title': {
                'text': title,
                'font': {'size': self.layout_config['title_font_size'], 'color': self.layout_config['font_color']}
            },
            'paper_bgcolor': self.layout_config['paper_bgcolor'],
            'plot_bgcolor': self.layout_config['plot_bgcolor'],
            'font': {'color': self.layout_config['font_color']},
            'height': height,
            'margin': {'l': 50, 'r': 50, 't': 50, 'b': 50},
            'showlegend': True,
            'legend': {
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1
            }
        }

    def create_candlestick_chart(
        self,
        timestamps: List[datetime],
        opens: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[int],
        ticker: str = "",
        show_volume: bool = True,
        height: int = 500
    ) -> go.Figure:
        """
        Create a candlestick chart with volume bars.

        Args:
            timestamps: List of datetime objects
            opens: List of opening prices
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices
            volumes: List of volume values
            ticker: Stock ticker for title
            show_volume: Whether to show volume subplot
            height: Chart height

        Returns:
            Plotly Figure object
        """
        if show_volume:
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
                subplot_titles=('', 'Volume')
            )
        else:
            fig = go.Figure()

        # Determine candle colors
        colors = []
        for close, open_price in zip(closes, opens):
            if close >= open_price:
                colors.append(self.config.colors['up'])
            else:
                colors.append(self.config.colors['down'])

        # Add candlestick trace
        fig.add_trace(
            go.Candlestick(
                x=timestamps,
                open=opens,
                high=highs,
                low=lows,
                close=closes,
                name='OHLC',
                increasing_line_color=self.config.colors['up'],
                decreasing_line_color=self.config.colors['down'],
                increasing_fillcolor=self.config.colors['up'],
                decreasing_fillcolor=self.config.colors['down']
            ),
            row=1 if show_volume else 1,
            col=1
        )

        # Add volume bars
        if show_volume and volumes:
            fig.add_trace(
                go.Bar(
                    x=timestamps,
                    y=volumes,
                    name='Volume',
                    marker_color=colors,
                    opacity=0.7
                ),
                row=2, col=1
            )

        # Update layout
        title = f"{ticker} - Candlestick Chart" if ticker else "Candlestick Chart"
        fig.update_layout(
            **self._get_layout(title, height),
            xaxis_rangeslider_visible=False
        )

        # Update axes
        fig.update_xaxes(
            showgrid=True,
            gridcolor=self.layout_config['gridcolor'],
            row=1 if show_volume else 1, col=1
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor=self.layout_config['gridcolor'],
            row=1 if show_volume else 1, col=1
        )

        if show_volume:
            fig.update_yaxes(
                showgrid=False,
                row=2, col=1
            )

        return fig

    def create_line_chart(
        self,
        timestamps: List[datetime],
        values: List[float],
        name: str = "Price",
        color: Optional[str] = None,
        show_area: bool = False,
        height: int = 400
    ) -> go.Figure:
        """
        Create a line chart.

        Args:
            timestamps: List of datetime objects
            values: List of values
            name: Line name for legend
            color: Custom line color
            show_area: Whether to show area fill
            height: Chart height

        Returns:
            Plotly Figure object
        """
        fig = go.Figure()

        line_color = color or self.config.colors['primary']

        if show_area:
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=values,
                    name=name,
                    fill='tozeroy',
                    fillcolor=self._hex_to_rgba(line_color, 0.2),
                    line=dict(color=line_color, width=2)
                )
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=values,
                    name=name,
                    mode='lines',
                    line=dict(color=line_color, width=2)
                )
            )

        fig.update_layout(**self._get_layout(name, height))

        fig.update_xaxes(
            showgrid=True,
            gridcolor=self.layout_config['gridcolor']
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor=self.layout_config['gridcolor']
        )

        return fig

    def create_score_gauge(
        self,
        score: int,
        signal: str,
        height: int = 200
    ) -> go.Figure:
        """
        Create a gauge chart for score display.

        Args:
            score: Score value (0-100)
            signal: Trading signal
            height: Chart height

        Returns:
            Plotly Figure object
        """
        # Determine color based on signal
        if signal in ['STRONG BUY', 'BUY']:
            color = self.config.colors['up']
        elif signal in ['SELL', 'STRONG SELL']:
            color = self.config.colors['down']
        else:
            color = self.config.colors['neutral']

        fig = go.Figure()

        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=score,
                title={'text': f"Score: {signal}", 'font': {'size': 14, 'color': self.layout_config['font_color']}},
                number={'font': {'size': 48, 'color': color}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': self.layout_config['font_color']},
                    'bar': {'color': color},
                    'bgcolor': self.layout_config['paper_bgcolor'],
                    'borderwidth': 2,
                    'bordercolor': self.layout_config['gridcolor'],
                    'steps': [
                        {'range': [0, 30], 'color': self.config.colors['down']},
                        {'range': [30, 50], 'color': '#FFA500'},
                        {'range': [50, 70], 'color': '#FFFF00'},
                        {'range': [70, 85], 'color': '#90EE90'},
                        {'range': [85, 100], 'color': self.config.colors['up']}
                    ],
                    'threshold': {
                        'line': {'color': color, 'width': 4},
                        'thickness': 0.75,
                        'value': score
                    }
                }
            )
        )

        fig.update_layout(
            paper_bgcolor=self.layout_config['paper_bgcolor'],
            plot_bgcolor=self.layout_config['plot_bgcolor'],
            height=height,
            margin={'l': 20, 'r': 20, 't': 50, 'b': 20}
        )

        return fig

    def create_score_breakdown_chart(
        self,
        breakdown: Dict[str, float],
        height: int = 300
    ) -> go.Figure:
        """
        Create a radar/spider chart for score breakdown.

        Args:
            breakdown: Dictionary with component names and scores
            height: Chart height

        Returns:
            Plotly Figure object
        """
        categories = list(breakdown.keys())
        values = list(breakdown.values())
        values.append(values[0])  # Close the polygon
        categories.append(categories[0])

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                fillcolor=self._hex_to_rgba(self.config.colors['primary'], 0.2),
                line=dict(color=self.config.colors['primary'], width=2),
                name='Score Breakdown'
            )
        )

        fig.update_layout(
            polar=dict(
                bgcolor=self.layout_config['paper_bgcolor'],
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont={'color': self.layout_config['font_color']}
                ),
                angularaxis=dict(
                    tickfont={'color': self.layout_config['font_color']}
                )
            ),
            paper_bgcolor=self.layout_config['paper_bgcolor'],
            height=height,
            showlegend=False
        )

        return fig

    def create_comparison_bar_chart(
        self,
        data: Dict[str, float],
        title: str = "Comparison",
        orientation: str = 'v',
        height: int = 400
    ) -> go.Figure:
        """
        Create a bar chart for comparing values.

        Args:
            data: Dictionary with labels and values
            title: Chart title
            orientation: 'v' for vertical, 'h' for horizontal
            height: Chart height

        Returns:
            Plotly Figure object
        """
        labels = list(data.keys())
        values = list(data.values())

        # Determine colors based on values
        colors = []
        for v in values:
            if v > 0:
                colors.append(self.config.colors['up'])
            elif v < 0:
                colors.append(self.config.colors['down'])
            else:
                colors.append(self.config.colors['neutral'])

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=labels if orientation == 'v' else values,
                y=values if orientation == 'v' else labels,
                orientation=orientation,
                marker_color=colors,
                text=[f"{v:.1f}" for v in values],
                textposition='auto'
            )
        )

        fig.update_layout(**self._get_layout(title, height))

        fig.update_xaxes(
            showgrid=True,
            gridcolor=self.layout_config['gridcolor']
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor=self.layout_config['gridcolor']
        )

        return fig

    def create_metrics_cards(
        self,
        metrics: Dict[str, Any],
        height: int = 150
    ) -> go.Figure:
        """
        Create a metrics display cards.

        Args:
            metrics: Dictionary with metric names and values
            height: Card height

        Returns:
            Plotly Figure object
        """
        fig = go.Figure()

        # Create table for metrics
        headers = list(metrics.keys())
        values = [str(v) for v in metrics.values()]

        fig.add_trace(
            go.Table(
                header=dict(
                    values=headers,
                    fill_color=self.config.colors['primary'],
                    align='center',
                    font=dict(size=12, color='white')
                ),
                cells=dict(
                    values=[values],
                    fill_color=[[self.layout_config['paper_bgcolor']] * len(values)],
                    align='center',
                    font=dict(size=14, color=self.layout_config['font_color'])
                )
            )
        )

        fig.update_layout(
            paper_bgcolor=self.layout_config['paper_bgcolor'],
            height=height,
            margin={'l': 10, 'r': 10, 't': 10, 'b': 10}
        )

        return fig

    def create_volume_chart(
        self,
        timestamps: List[datetime],
        volumes: List[int],
        avg_volume: float,
        height: int = 300
    ) -> go.Figure:
        """
        Create a volume bar chart with average line.

        Args:
            timestamps: List of datetime objects
            volumes: List of volume values
            avg_volume: Average volume for reference line
            height: Chart height

        Returns:
            Plotly Figure object
        """
        fig = go.Figure()

        # Add volume bars
        fig.add_trace(
            go.Bar(
                x=timestamps,
                y=volumes,
                name='Volume',
                marker_color=self.config.colors['primary'],
                opacity=0.7
            )
        )

        # Add average line
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=[avg_volume] * len(timestamps),
                name='Average',
                mode='lines',
                line=dict(color=self.config.colors['accent'], width=2, dash='dash')
            )
        )

        fig.update_layout(
            **self._get_layout("Volume Analysis", height),
            xaxis_rangeslider_visible=False
        )

        fig.update_xaxes(
            showgrid=True,
            gridcolor=self.layout_config['gridcolor']
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor=self.layout_config['gridcolor']
        )

        return fig

    def create_price_change_chart(
        self,
        data: List[Dict],
        height: int = 300
    ) -> go.Figure:
        """
        Create a horizontal bar chart for price changes.

        Args:
            data: List of dictionaries with 'ticker', 'name', 'change_pct'
            height: Chart height

        Returns:
            Plotly Figure object
        """
        tickers = [d['ticker'] for d in data]
        changes = [d['change_pct'] for d in data]

        # Color based on positive/negative
        colors = [
            self.config.colors['up'] if c >= 0 else self.config.colors['down']
            for c in changes
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                y=tickers,
                x=changes,
                orientation='h',
                marker_color=colors,
                text=[f"{c:+.2f}%" for c in changes],
                textposition='auto'
            )
        )

        fig.update_layout(
            **self._get_layout("Price Changes", height),
            xaxis_title="Change %",
            yaxis_title="Ticker"
        )

        fig.update_xaxes(
            showgrid=True,
            gridcolor=self.layout_config['gridcolor'],
            zeroline=True,
            zerolinecolor=self.layout_config['gridcolor']
        )
        fig.update_yaxes(
            showgrid=False
        )

        return fig

    def create_market_overview_pie(
        self,
        gainers: int,
        losers: int,
        unchanged: int,
        height: int = 300
    ) -> go.Figure:
        """
        Create a pie chart for market overview.

        Args:
            gainers: Number of gainers
            losers: Number of losers
            unchanged: Number of unchanged
            height: Chart height

        Returns:
            Plotly Figure object
        """
        fig = go.Figure()

        fig.add_trace(
            go.Pie(
                labels=['Gainers', 'Losers', 'Unchanged'],
                values=[gainers, losers, unchanged],
                marker=dict(
                    colors=[
                        self.config.colors['up'],
                        self.config.colors['down'],
                        self.config.colors['neutral']
                    ]
                ),
                textinfo='label+percent',
                textposition='inside',
                hole=0.4
            )
        )

        fig.update_layout(
            paper_bgcolor=self.layout_config['paper_bgcolor'],
            height=height,
            margin={'l': 20, 'r': 20, 't': 50, 'b': 20},
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.2,
                xanchor='center',
                x=0.5
            )
        )

        return fig

    def create_strategy_comparison(
        self,
        strategies: List[Dict],
        height: int = 400
    ) -> go.Figure:
        """
        Create a grouped bar chart comparing strategies.

        Args:
            strategies: List of strategy dictionaries
            height: Chart height

        Returns:
            Plotly Figure object
        """
        strategy_names = [s['strategy'] for s in strategies]
        targets = [s['target_pct'] for s in strategies]
        stop_losses = [s['stop_loss_pct'] for s in strategies]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                name='Target %',
                x=strategy_names,
                y=targets,
                marker_color=self.config.colors['up']
            )
        )

        fig.add_trace(
            go.Bar(
                name='Stop Loss %',
                x=strategy_names,
                y=stop_losses,
                marker_color=self.config.colors['down']
            )
        )

        fig.update_layout(
            **self._get_layout("Strategy Comparison", height),
            barmode='group',
            xaxis_title="Strategy",
            yaxis_title="Percentage"
        )

        fig.update_xaxes(
            showgrid=False
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor=self.layout_config['gridcolor']
        )

        return fig


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'VisualizationLayer',
    'ChartConfig'
]
