"""
Tests for Session Engine Module
================================
"""

import pytest
from datetime import datetime, time, timedelta
from modules.session_engine import SessionEngine, SessionStatus, SessionInfo


class TestSessionEngine:
    """Test cases for SessionEngine class."""

    @pytest.fixture
    def engine(self):
        """Create a SessionEngine instance for testing."""
        return SessionEngine()

    def test_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert engine.timezone_offset == 7
        assert engine.tz is not None

    def test_get_current_time_wib(self, engine):
        """Test getting current time in WIB."""
        current_time = engine.get_current_time_wib()
        assert current_time is not None
        assert current_time.tzinfo is not None

    def test_is_weekend(self, engine):
        """Test weekend detection."""
        # Saturday
        saturday = datetime(2024, 6, 15, 12, 0, 0)
        assert engine.is_weekend(saturday) is True

        # Sunday
        sunday = datetime(2024, 6, 16, 12, 0, 0)
        assert engine.is_weekend(sunday) is True

        # Monday
        monday = datetime(2024, 6, 17, 12, 0, 0)
        assert engine.is_weekend(monday) is False

    def test_is_holiday(self, engine):
        """Test holiday detection."""
        # Christmas (known holiday)
        christmas = datetime(2024, 12, 25, 12, 0, 0)
        assert engine.is_holiday(christmas) is True

        # Regular day
        regular_day = datetime(2024, 6, 17, 12, 0, 0)
        assert engine.is_holiday(regular_day) is False

    def test_get_session_status_pre_market(self, engine):
        """Test pre-market session detection."""
        # 07:30 WIB on a weekday
        pre_market_time = datetime(2024, 6, 17, 7, 30, 0)
        status = engine.get_session_status(pre_market_time)
        assert status == SessionStatus.PRE_MARKET

    def test_get_session_status_open(self, engine):
        """Test regular session detection."""
        # 10:00 WIB on a weekday
        open_time = datetime(2024, 6, 17, 10, 0, 0)
        status = engine.get_session_status(open_time)
        assert status == SessionStatus.OPEN

    def test_get_session_status_after_hours(self, engine):
        """Test after-hours session detection."""
        # 15:40 WIB on a weekday
        after_hours_time = datetime(2024, 6, 17, 15, 40, 0)
        status = engine.get_session_status(after_hours_time)
        assert status == SessionStatus.AFTER_HOURS

    def test_get_session_status_closed(self, engine):
        """Test closed session detection."""
        # 20:00 WIB on a weekday
        closed_time = datetime(2024, 6, 17, 20, 0, 0)
        status = engine.get_session_status(closed_time)
        assert status == SessionStatus.CLOSED

    def test_get_session_status_weekend(self, engine):
        """Test weekend session detection."""
        # Saturday
        saturday = datetime(2024, 6, 15, 12, 0, 0)
        status = engine.get_session_status(saturday)
        assert status == SessionStatus.WEEKEND

    def test_get_session_info(self, engine):
        """Test getting comprehensive session info."""
        # Monday 10:00 WIB
        monday_10am = datetime(2024, 6, 17, 10, 0, 0)
        info = engine.get_session_info(monday_10am)

        assert isinstance(info, SessionInfo)
        assert info.status == SessionStatus.OPEN
        assert info.is_trading_active is True
        assert info.session_message is not None
        assert info.next_session_change is not None

    def test_format_time_remaining(self, engine):
        """Test time formatting."""
        # Test hours and minutes
        td = timedelta(hours=2, minutes=30)
        formatted = engine.format_time_remaining(td)
        assert formatted == "2h 30m"

        # Test minutes only
        td = timedelta(minutes=45)
        formatted = engine.format_time_remaining(td)
        assert formatted == "45m"

        # Test zero
        td = timedelta(0)
        formatted = engine.format_time_remaining(td)
        assert formatted == "Now"

    def test_get_market_summary(self, engine):
        """Test market summary generation."""
        summary = engine.get_market_summary()

        assert 'status' in summary
        assert 'status_display' in summary
        assert 'is_trading_active' in summary
        assert 'session_message' in summary
        assert 'time_until_change' in summary
        assert 'next_session' in summary

    def test_get_next_session_change(self, engine):
        """Test next session change calculation."""
        # Monday 10:00 WIB - next change should be regular end
        monday_10am = datetime(2024, 6, 17, 10, 0, 0)
        next_change = engine.get_next_session_change(monday_10am)

        assert next_change is not None
        assert next_change.hour == 15
        assert next_change.minute == 30

    def test_trading_hours_configuration(self, engine):
        """Test trading hours are correctly configured."""
        assert engine.pre_market_start == time(7, 0)
        assert engine.regular_start == time(8, 30)
        assert engine.regular_end == time(15, 30)
        assert engine.after_hours_end == time(15, 50)


class TestSessionStatus:
    """Test cases for SessionStatus enum."""

    def test_session_status_values(self):
        """Test all session status values exist."""
        assert SessionStatus.PRE_MARKET.value == "pre_market"
        assert SessionStatus.OPEN.value == "open"
        assert SessionStatus.AFTER_HOURS.value == "after_hours"
        assert SessionStatus.CLOSED.value == "closed"
        assert SessionStatus.WEEKEND.value == "weekend"
        assert SessionStatus.HOLIDAY.value == "holiday"


class TestSessionInfo:
    """Test cases for SessionInfo dataclass."""

    def test_session_info_creation(self):
        """Test SessionInfo creation."""
        info = SessionInfo(
            status=SessionStatus.OPEN,
            status_display="Regular Session",
            is_trading_active=True,
            next_session_change=datetime(2024, 6, 17, 15, 30),
            session_message="Regular Trading Session Active",
            time_until_change=timedelta(hours=5, minutes=30)
        )

        assert info.status == SessionStatus.OPEN
        assert info.is_trading_active is True
        assert info.time_until_change == timedelta(hours=5, minutes=30)
