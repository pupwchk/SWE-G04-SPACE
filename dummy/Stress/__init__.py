"""
SPACE Stress Detection Module

Real-time HRV-based stress monitoring for smart home automation
"""

from .hrv_calculator import (
    HRVCalculator,
    RollingHRVCalculator,
    HRVMetrics
)

from .stress_detector import (
    StressDetector,
    StressLevel,
    StressAssessment
)

from .realtime_monitor import (
    RealtimeStressMonitor,
    StressMonitorSession
)

__all__ = [
    # HRV Calculation
    'HRVCalculator',
    'RollingHRVCalculator',
    'HRVMetrics',

    # Stress Detection
    'StressDetector',
    'StressLevel',
    'StressAssessment',

    # Real-time Monitoring
    'RealtimeStressMonitor',
    'StressMonitorSession'
]

__version__ = '1.0.0'
