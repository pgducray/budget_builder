"""
Common types for analytics modules.
"""
from dataclasses import dataclass
from datetime import date


@dataclass
class AnalysisPeriod:
    """Data class for analysis time periods."""
    start_date: date
    end_date: date
    name: str = ""
