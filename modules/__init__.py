"""
IHSG Stock Screener - Modules Package
=======================================
Core modules for the stock screener application.
"""

from .session_engine import SessionEngine, SessionStatus, SessionInfo
from .data_fetcher import DataFetcher, StockData, CandlestickData, BatchFetchResult
from .scoring_engine import ScoringEngine, ScoredStock, ScoreBreakdown, SignalType
from .recommendation_engine import (
    RecommendationEngine,
    StockRecommendation,
    PriceLevels,
    StrategyMetrics,
    StrategyType,
    RiskLevel
)
from .visualization_layer import VisualizationLayer, ChartConfig
from .bsjp_detector import BSJPDetector, BSJPStock, GapType
from .bpjs_detector import BPJSDetector, BPJSStock, BPJSSignal

__all__ = [
    # Session Engine
    'SessionEngine',
    'SessionStatus',
    'SessionInfo',
    # Data Fetcher
    'DataFetcher',
    'StockData',
    'CandlestickData',
    'BatchFetchResult',
    # Scoring Engine
    'ScoringEngine',
    'ScoredStock',
    'ScoreBreakdown',
    'SignalType',
    # Recommendation Engine
    'RecommendationEngine',
    'StockRecommendation',
    'PriceLevels',
    'StrategyMetrics',
    'StrategyType',
    'RiskLevel',
    # Visualization Layer
    'VisualizationLayer',
    'ChartConfig',
    # BSJP Detector
    'BSJPDetector',
    'BSJPStock',
    'GapType',
    # BPJS Detector
    'BPJSDetector',
    'BPJSStock',
    'BPJSSignal'
]

__version__ = '1.0.0'
