"""
IHSG Stock Screener - Session Engine Module
============================================
Handles trading session detection for Indonesian stock market (IDX).
Determines if market is open, closed, pre-market, or after-hours.
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from enum import Enum
from typing import Optional

# Try to import timezone library (prefer zoneinfo from stdlib, fallback to pytz)
try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo('Asia/Jakarta')
except ImportError:
    try:
        import pytz
        TZ = pytz.timezone('Asia/Jakarta')
    except ImportError:
        # Fallback: use UTC+7 directly
        TZ = None


class SessionStatus(Enum):
    """Enumeration of possible trading session states."""
    PRE_MARKET = "pre_market"
    OPEN = "open"
    AFTER_HOURS = "after_hours"
    CLOSED = "closed"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"


@dataclass
class SessionInfo:
    """Data class containing session information."""
    status: SessionStatus
    status_display: str
    is_trading_active: bool
    next_session_change: Optional[datetime]
    session_message: str
    time_until_change: Optional[timedelta] = None


class SessionEngine:
    """
    Session Engine for detecting Indonesian stock market trading sessions.

    Indonesian Stock Exchange (IDX) Trading Hours (WIB - UTC+7):
    - Pre-Market: 07:00 - 08:30
    - Regular Session: 08:30 - 15:30
    - After Hours: 15:30 - 15:50
    - Closed: 15:50 - 07:00 (next day)
    """

    def __init__(self, timezone_offset: int = 7):
        """
        Initialize the Session Engine.

        Args:
            timezone_offset: Offset from UTC for WIB timezone (default: 7)
        """
        self.timezone_offset = timezone_offset
        self.tz = TZ

        # Trading hours in local time (WIB)
        self.pre_market_start = time(7, 0)
        self.regular_start = time(8, 30)
        self.regular_end = time(15, 30)
        self.after_hours_end = time(15, 50)

        # Indonesian public holidays (simplified - add more as needed)
        self._holidays = self._load_holidays()

    def _load_holidays(self) -> set:
        """
        Load Indonesian stock market holidays.

        Returns:
            Set of dates that are holidays (YYYY-MM-DD format)
        """
        # Common Indonesian holidays affecting IDX
        holidays = set()

        # Add national holidays for current year (2024-2026)
        # New Year
        holidays.update([
            "2024-01-01", "2025-01-01", "2026-01-01",
            "2024-01-02", "2025-01-02", "2026-01-02",
        ])

        # Chinese New Year
        holidays.update([
            "2024-02-10", "2024-02-11", "2024-02-12",
            "2025-01-29", "2025-01-30", "2025-01-31",
            "2026-02-17", "2026-02-18", "2026-02-19",
        ])

        # Good Friday
        holidays.update([
            "2024-03-29",
            "2025-04-18",
            "2026-04-03",
        ])

        # Ascension Day
        holidays.update([
            "2024-05-09",
            "2025-05-29",
            "2026-05-14",
        ])

        # Eid al-Fitr (approximate - check actual dates)
        holidays.update([
            "2024-04-10", "2024-04-11", "2024-04-12", "2024-04-13", "2024-04-14",
            "2025-03-30", "2025-03-31", "2025-04-01", "2025-04-02", "2025-04-03",
            "2026-03-20", "2026-03-21", "2026-03-22", "2026-03-23", "2026-03-24",
        ])

        # Labour Day
        holidays.update([
            "2024-05-01", "2025-05-01", "2026-05-01",
        ])

        # Ascension of Jesus
        holidays.update([
            "2024-05-09", "2025-05-29", "2026-05-14",
        ])

        # Vesak Day
        holidays.update([
            "2024-05-23", "2025-05-12", "2026-05-04",
        ])

        # Eid al-Adha (approximate)
        holidays.update([
            "2024-06-16", "2024-06-17", "2024-06-18",
            "2025-06-06", "2025-06-07", "2025-06-08",
            "2026-05-26", "2026-05-27", "2026-05-28",
        ])

        # Independence Day
        holidays.update([
            "2024-08-17", "2025-08-17", "2026-08-17",
        ])

        # Islamic New Year
        holidays.update([
            "2024-07-07", "2025-06-26", "2026-06-15",
        ])

        # Christmas Eve
        holidays.update([
            "2024-12-24", "2025-12-24", "2026-12-24",
        ])

        # Christmas
        holidays.update([
            "2024-12-25", "2025-12-25", "2026-12-25",
        ])

        return holidays

    def get_current_time_wib(self) -> datetime:
        """
        Get current time in WIB (Jakarta) timezone.

        Returns:
            Current datetime in WIB
        """
        if self.tz is not None:
            return datetime.now().astimezone(self.tz)
        else:
            # Fallback: use UTC+7 directly
            utc_now = datetime.now(timezone.utc)
            return utc_now.astimezone(timezone(timedelta(hours=7)))

    def is_weekend(self, dt: datetime) -> bool:
        """
        Check if the given date is a weekend.

        Args:
            dt: Datetime to check

        Returns:
            True if Saturday or Sunday
        """
        return dt.weekday() >= 5  # 5 = Saturday, 6 = Sunday

    def is_holiday(self, dt: datetime) -> bool:
        """
        Check if the given date is a market holiday.

        Args:
            dt: Datetime to check

        Returns:
            True if the date is a holiday
        """
        date_str = dt.strftime("%Y-%m-%d")
        return date_str in self._holidays

    def get_session_status(self, dt: Optional[datetime] = None) -> SessionStatus:
        """
        Determine the trading session status for the given time.

        Args:
            dt: Datetime to check (defaults to current time)

        Returns:
            SessionStatus enum value
        """
        if dt is None:
            dt = self.get_current_time_wib()
        else:
            dt = dt.astimezone(self.tz)

        # Check for weekend
        if self.is_weekend(dt):
            return SessionStatus.WEEKEND

        # Check for holiday
        if self.is_holiday(dt):
            return SessionStatus.HOLIDAY

        # Get current time as time object
        current_time = dt.time()

        # Determine session based on time
        if current_time < self.pre_market_start:
            return SessionStatus.CLOSED
        elif current_time < self.regular_start:
            return SessionStatus.PRE_MARKET
        elif current_time <= self.regular_end:
            return SessionStatus.OPEN
        elif current_time <= self.after_hours_end:
            return SessionStatus.AFTER_HOURS
        else:
            return SessionStatus.CLOSED

    def get_next_session_change(self, dt: Optional[datetime] = None) -> datetime:
        """
        Calculate the next session change time.

        Args:
            dt: Current datetime (defaults to now)

        Returns:
            Datetime of next session change
        """
        if dt is None:
            dt = self.get_current_time_wib()
        else:
            dt = dt.astimezone(self.tz)

        current_status = self.get_session_status(dt)
        current_time = dt.time()
        today = dt.date()

        if current_status == SessionStatus.CLOSED:
            # Next session is pre-market at 07:00
            if current_time >= self.after_hours_end:
                # After market close, next session is tomorrow 07:00
                next_date = today + timedelta(days=1)
                while self.is_weekend(datetime.combine(next_date, time(7, 0))) or \
                      self.is_holiday(datetime.combine(next_date, time(7, 0))):
                    next_date += timedelta(days=1)
                return datetime.combine(next_date, self.pre_market_start).replace(tzinfo=self.tz)
            else:
                # Before market open, pre-market starts at 07:00
                return datetime.combine(today, self.pre_market_start).replace(tzinfo=self.tz)

        elif current_status == SessionStatus.PRE_MARKET:
            return datetime.combine(today, self.regular_start).replace(tzinfo=self.tz)

        elif current_status == SessionStatus.OPEN:
            return datetime.combine(today, self.regular_end).replace(tzinfo=self.tz)

        elif current_status == SessionStatus.AFTER_HOURS:
            return datetime.combine(today, self.after_hours_end).replace(tzinfo=self.tz)

        else:  # WEEKEND or HOLIDAY
            # Next trading day at 07:00
            next_date = today + timedelta(days=1)
            while self.is_weekend(datetime.combine(next_date, time(7, 0))) or \
                  self.is_holiday(datetime.combine(next_date, time(7, 0))):
                next_date += timedelta(days=1)
            return datetime.combine(next_date, self.pre_market_start).replace(tzinfo=self.tz)

    def get_session_info(self, dt: Optional[datetime] = None) -> SessionInfo:
        """
        Get comprehensive session information.

        Args:
            dt: Datetime to check (defaults to now)

        Returns:
            SessionInfo dataclass with all session details
        """
        if dt is None:
            dt = self.get_current_time_wib()
        else:
            dt = dt.astimezone(self.tz)

        status = self.get_session_status(dt)
        next_change = self.get_next_session_change(dt)
        time_until = next_change - dt

        status_messages = {
            SessionStatus.PRE_MARKET: "Pre-Market Session Active",
            SessionStatus.OPEN: "Regular Trading Session Active",
            SessionStatus.AFTER_HOURS: "After Hours Trading Active",
            SessionStatus.CLOSED: "Market Closed",
            SessionStatus.WEEKEND: "Market Closed (Weekend)",
            SessionStatus.HOLIDAY: "Market Closed (Holiday)"
        }

        is_trading = status in [SessionStatus.PRE_MARKET, SessionStatus.OPEN, SessionStatus.AFTER_HOURS]

        return SessionInfo(
            status=status,
            status_display=status.name.replace('_', ' ').title(),
            is_trading_active=is_trading,
            next_session_change=next_change,
            session_message=status_messages.get(status, "Unknown Session"),
            time_until_change=time_until
        )

    def get_time_until_session(self, target_status: SessionStatus, dt: Optional[datetime] = None) -> timedelta:
        """
        Calculate time until a specific session status begins.

        Args:
            target_status: The target session status
            dt: Current datetime (defaults to now)

        Returns:
            Timedelta until the target session begins
        """
        if dt is None:
            dt = self.get_current_time_wib()
        else:
            dt = dt.astimezone(self.tz)

        # Find when the target status will be active
        current_status = self.get_session_status(dt)

        if current_status == target_status:
            return timedelta(0)

        # Iterate through time to find next occurrence
        check_dt = dt
        for _ in range(1440):  # Check up to 24 hours (1440 minutes)
            check_dt += timedelta(minutes=1)
            if self.get_session_status(check_dt) == target_status:
                return check_dt - dt

        return timedelta(days=1)  # Default to 1 day if not found

    def format_time_remaining(self, td: timedelta) -> str:
        """
        Format a timedelta into a human-readable string.

        Args:
            td: Timedelta to format

        Returns:
            Formatted string like "2h 30m" or "Market Open"
        """
        if td.total_seconds() <= 0:
            return "Now"

        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes = remainder // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def get_market_summary(self) -> dict:
        """
        Get a summary of market status for display.

        Returns:
            Dictionary with market status information
        """
        session_info = self.get_session_info()

        return {
            'status': session_info.status.value,
            'status_display': session_info.status_display,
            'is_trading_active': session_info.is_trading_active,
            'session_message': session_info.session_message,
            'time_until_change': self.format_time_remaining(session_info.time_until_change) if session_info.time_until_change else None,
            'next_session': session_info.next_session_change.strftime('%H:%M') if session_info.next_session_change else None
        }


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'SessionEngine',
    'SessionStatus',
    'SessionInfo'
]
