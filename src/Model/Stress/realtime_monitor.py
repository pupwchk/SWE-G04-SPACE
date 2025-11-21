"""
Real-time HRV and Stress Monitoring

Provides real-time monitoring of heart rate data to calculate HRV
and detect stress levels continuously.
"""

from typing import Optional, Callable, List
from datetime import datetime, timedelta
from collections import deque
import time

from hrv_calculator import RollingHRVCalculator, HRVMetrics
from stress_detector import StressDetector, StressAssessment, StressLevel


class RealtimeStressMonitor:
    """
    Real-time stress monitoring from continuous heart rate data
    """

    def __init__(self,
                 window_size: int = 60,
                 update_interval: int = 1,
                 on_stress_change: Optional[Callable[[StressAssessment], None]] = None,
                 on_high_stress_alert: Optional[Callable[[StressAssessment], None]] = None):
        """
        Initialize real-time stress monitor

        Args:
            window_size: Number of RR intervals for HRV calculation (default: 60)
            update_interval: Minutes between stress assessments (default: 1)
            on_stress_change: Callback when stress level changes
            on_high_stress_alert: Callback when high stress is detected
        """
        self.hrv_calculator = RollingHRVCalculator(window_size=window_size)
        self.stress_detector = StressDetector()
        self.update_interval = update_interval

        self.on_stress_change = on_stress_change
        self.on_high_stress_alert = on_high_stress_alert

        self.current_stress: Optional[StressAssessment] = None
        self.last_update_time: Optional[datetime] = None
        self.stress_history: deque = deque(maxlen=100)  # Keep last 100 assessments

    def add_heart_rate(self, heart_rate: float, timestamp: Optional[datetime] = None) -> Optional[StressAssessment]:
        """
        Add a new heart rate measurement

        Args:
            heart_rate: Heart rate in BPM
            timestamp: Timestamp of the measurement (default: now)

        Returns:
            StressAssessment if stress was updated, None otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Add heart rate to rolling calculator
        hrv_metrics = self.hrv_calculator.add_heart_rate(heart_rate)

        # Check if we should update stress assessment
        if hrv_metrics is not None:
            should_update = (
                self.last_update_time is None or
                (timestamp - self.last_update_time).total_seconds() >= self.update_interval * 60
            )

            if should_update:
                return self._update_stress_assessment(hrv_metrics)

        return None

    def _update_stress_assessment(self, hrv_metrics: HRVMetrics) -> StressAssessment:
        """
        Update stress assessment from HRV metrics

        Args:
            hrv_metrics: HRV metrics to assess

        Returns:
            Updated stress assessment
        """
        # Detect stress level
        new_assessment = self.stress_detector.detect_stress(hrv_metrics)

        # Check if stress level changed
        if self.current_stress is not None:
            if new_assessment.stress_level != self.current_stress.stress_level:
                if self.on_stress_change:
                    self.on_stress_change(new_assessment)

        # Check for high stress alert
        if new_assessment.stress_level in [StressLevel.HIGH, StressLevel.VERY_HIGH]:
            if self.on_high_stress_alert:
                self.on_high_stress_alert(new_assessment)

        # Update current stress
        self.current_stress = new_assessment
        self.last_update_time = new_assessment.timestamp
        self.stress_history.append(new_assessment)

        return new_assessment

    def get_current_stress(self) -> Optional[StressAssessment]:
        """
        Get current stress assessment

        Returns:
            Current stress assessment or None if not yet available
        """
        return self.current_stress

    def get_stress_trend(self, duration_minutes: int = 60) -> List[StressAssessment]:
        """
        Get stress assessments from the last N minutes

        Args:
            duration_minutes: Duration in minutes to look back

        Returns:
            List of stress assessments within the time window
        """
        if not self.stress_history:
            return []

        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        return [
            assessment for assessment in self.stress_history
            if assessment.timestamp >= cutoff_time
        ]

    def get_average_stress_score(self, duration_minutes: int = 60) -> Optional[float]:
        """
        Get average stress score over the last N minutes

        Args:
            duration_minutes: Duration in minutes to average over

        Returns:
            Average stress score or None if no data available
        """
        trend = self.get_stress_trend(duration_minutes)
        if not trend:
            return None

        return sum(a.stress_score for a in trend) / len(trend)

    def is_stress_increasing(self, duration_minutes: int = 30) -> bool:
        """
        Check if stress is increasing over the last N minutes

        Args:
            duration_minutes: Duration in minutes to analyze

        Returns:
            True if stress is increasing, False otherwise
        """
        trend = self.get_stress_trend(duration_minutes)
        if len(trend) < 3:
            return False

        # Calculate linear trend
        scores = [a.stress_score for a in trend]
        n = len(scores)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(scores) / n

        # Calculate slope
        numerator = sum((x[i] - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return False

        slope = numerator / denominator

        # Positive slope = increasing stress
        return slope > 2  # Threshold: stress increasing by >2 points per measurement

    def reset(self):
        """Reset the monitor"""
        self.hrv_calculator.reset()
        self.current_stress = None
        self.last_update_time = None
        self.stress_history.clear()


class StressMonitorSession:
    """
    Context manager for stress monitoring sessions
    """

    def __init__(self, monitor: RealtimeStressMonitor):
        """
        Initialize session

        Args:
            monitor: Stress monitor to use
        """
        self.monitor = monitor
        self.session_start: Optional[datetime] = None
        self.session_end: Optional[datetime] = None

    def __enter__(self):
        """Start monitoring session"""
        self.session_start = datetime.now()
        self.monitor.reset()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End monitoring session"""
        self.session_end = datetime.now()

    def get_session_summary(self) -> dict:
        """
        Get summary of the monitoring session

        Returns:
            Dictionary with session statistics
        """
        if not self.session_start:
            return {}

        duration = (self.session_end or datetime.now()) - self.session_start
        all_assessments = list(self.monitor.stress_history)

        if not all_assessments:
            return {
                'session_start': self.session_start.isoformat(),
                'session_end': (self.session_end or datetime.now()).isoformat(),
                'duration_minutes': duration.total_seconds() / 60,
                'num_assessments': 0
            }

        stress_scores = [a.stress_score for a in all_assessments]
        stress_levels = [a.stress_level for a in all_assessments]

        return {
            'session_start': self.session_start.isoformat(),
            'session_end': (self.session_end or datetime.now()).isoformat(),
            'duration_minutes': duration.total_seconds() / 60,
            'num_assessments': len(all_assessments),
            'average_stress_score': sum(stress_scores) / len(stress_scores),
            'min_stress_score': min(stress_scores),
            'max_stress_score': max(stress_scores),
            'stress_level_distribution': {
                'very_low': sum(1 for l in stress_levels if l == StressLevel.VERY_LOW),
                'low': sum(1 for l in stress_levels if l == StressLevel.LOW),
                'moderate': sum(1 for l in stress_levels if l == StressLevel.MODERATE),
                'high': sum(1 for l in stress_levels if l == StressLevel.HIGH),
                'very_high': sum(1 for l in stress_levels if l == StressLevel.VERY_HIGH)
            },
            'high_stress_episodes': sum(1 for l in stress_levels
                                       if l in [StressLevel.HIGH, StressLevel.VERY_HIGH])
        }
