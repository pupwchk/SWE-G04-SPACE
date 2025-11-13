"""
HRV (Heart Rate Variability) Calculator

Calculates various HRV metrics from RR interval data:
- SDNN (Standard Deviation of NN intervals)
- RMSSD (Root Mean Square of Successive Differences)
- pNN50 (Percentage of successive RR intervals that differ by more than 50ms)
- Heart Rate from RR intervals

Reference:
- Task Force of the European Society of Cardiology and the North American Society of Pacing and Electrophysiology (1996)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class HRVMetrics:
    """Container for HRV metrics"""
    sdnn: float  # Standard deviation of NN intervals (ms)
    rmssd: float  # Root mean square of successive differences (ms)
    pnn50: float  # Percentage of successive differences > 50ms
    mean_rr: float  # Mean RR interval (ms)
    mean_hr: float  # Mean heart rate (bpm)
    timestamp: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'sdnn': self.sdnn,
            'rmssd': self.rmssd,
            'pnn50': self.pnn50,
            'mean_rr': self.mean_rr,
            'mean_hr': self.mean_hr,
            'timestamp': self.timestamp.isoformat()
        }


class HRVCalculator:
    """
    Calculates HRV metrics from heart rate or RR interval data
    """

    @staticmethod
    def heart_rate_to_rr_intervals(heart_rates: List[float]) -> List[float]:
        """
        Convert heart rate (bpm) to RR intervals (ms)

        Args:
            heart_rates: List of heart rates in beats per minute

        Returns:
            List of RR intervals in milliseconds
        """
        rr_intervals = []
        for hr in heart_rates:
            if hr > 0:
                # RR interval (ms) = 60000 / HR (bpm)
                rr = 60000.0 / hr
                rr_intervals.append(rr)
        return rr_intervals

    @staticmethod
    def filter_outliers(rr_intervals: List[float],
                       threshold: float = 0.2) -> List[float]:
        """
        Filter outliers from RR intervals using successive difference threshold

        Args:
            rr_intervals: List of RR intervals in milliseconds
            threshold: Maximum allowed relative change (default: 20%)

        Returns:
            Filtered list of RR intervals
        """
        if len(rr_intervals) < 2:
            return rr_intervals

        filtered = [rr_intervals[0]]

        for i in range(1, len(rr_intervals)):
            prev_rr = filtered[-1]
            curr_rr = rr_intervals[i]

            # Check if change is within threshold
            relative_change = abs(curr_rr - prev_rr) / prev_rr

            if relative_change <= threshold:
                filtered.append(curr_rr)
            else:
                # Skip outlier, keep previous value
                pass

        return filtered

    @staticmethod
    def calculate_sdnn(rr_intervals: List[float]) -> float:
        """
        Calculate SDNN (Standard Deviation of NN intervals)

        Args:
            rr_intervals: List of RR intervals in milliseconds

        Returns:
            SDNN value in milliseconds
        """
        if len(rr_intervals) < 2:
            return 0.0

        return float(np.std(rr_intervals, ddof=1))

    @staticmethod
    def calculate_rmssd(rr_intervals: List[float]) -> float:
        """
        Calculate RMSSD (Root Mean Square of Successive Differences)

        Args:
            rr_intervals: List of RR intervals in milliseconds

        Returns:
            RMSSD value in milliseconds
        """
        if len(rr_intervals) < 2:
            return 0.0

        # Calculate successive differences
        successive_diffs = np.diff(rr_intervals)

        # Square the differences
        squared_diffs = successive_diffs ** 2

        # Calculate mean and take square root
        rmssd = float(np.sqrt(np.mean(squared_diffs)))

        return rmssd

    @staticmethod
    def calculate_pnn50(rr_intervals: List[float]) -> float:
        """
        Calculate pNN50 (Percentage of successive differences > 50ms)

        Args:
            rr_intervals: List of RR intervals in milliseconds

        Returns:
            pNN50 percentage (0-100)
        """
        if len(rr_intervals) < 2:
            return 0.0

        # Calculate successive differences
        successive_diffs = np.abs(np.diff(rr_intervals))

        # Count differences > 50ms
        nn50_count = np.sum(successive_diffs > 50)

        # Calculate percentage
        pnn50 = (nn50_count / len(successive_diffs)) * 100

        return float(pnn50)

    @classmethod
    def calculate_hrv_metrics(cls,
                             rr_intervals: List[float],
                             filter_outliers: bool = True,
                             timestamp: Optional[datetime] = None) -> HRVMetrics:
        """
        Calculate all HRV metrics from RR intervals

        Args:
            rr_intervals: List of RR intervals in milliseconds
            filter_outliers: Whether to filter outliers (default: True)
            timestamp: Timestamp for the metrics (default: now)

        Returns:
            HRVMetrics object containing all calculated metrics
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Filter outliers if requested
        if filter_outliers and len(rr_intervals) > 2:
            rr_intervals = cls.filter_outliers(rr_intervals)

        # Calculate metrics
        if len(rr_intervals) < 2:
            return HRVMetrics(
                sdnn=0.0,
                rmssd=0.0,
                pnn50=0.0,
                mean_rr=0.0,
                mean_hr=0.0,
                timestamp=timestamp
            )

        mean_rr = float(np.mean(rr_intervals))
        mean_hr = 60000.0 / mean_rr if mean_rr > 0 else 0.0

        sdnn = cls.calculate_sdnn(rr_intervals)
        rmssd = cls.calculate_rmssd(rr_intervals)
        pnn50 = cls.calculate_pnn50(rr_intervals)

        return HRVMetrics(
            sdnn=sdnn,
            rmssd=rmssd,
            pnn50=pnn50,
            mean_rr=mean_rr,
            mean_hr=mean_hr,
            timestamp=timestamp
        )

    @classmethod
    def calculate_hrv_from_heart_rates(cls,
                                       heart_rates: List[float],
                                       filter_outliers: bool = True,
                                       timestamp: Optional[datetime] = None) -> HRVMetrics:
        """
        Calculate HRV metrics from heart rate data

        Args:
            heart_rates: List of heart rates in beats per minute
            filter_outliers: Whether to filter outliers (default: True)
            timestamp: Timestamp for the metrics (default: now)

        Returns:
            HRVMetrics object containing all calculated metrics
        """
        # Convert heart rates to RR intervals
        rr_intervals = cls.heart_rate_to_rr_intervals(heart_rates)

        # Calculate HRV metrics
        return cls.calculate_hrv_metrics(
            rr_intervals=rr_intervals,
            filter_outliers=filter_outliers,
            timestamp=timestamp
        )


class RollingHRVCalculator:
    """
    Calculates HRV metrics using a rolling window for real-time monitoring
    """

    def __init__(self, window_size: int = 60):
        """
        Initialize rolling HRV calculator

        Args:
            window_size: Number of RR intervals to use for calculation (default: 60)
        """
        self.window_size = window_size
        self.rr_buffer: List[float] = []
        self.calculator = HRVCalculator()

    def add_rr_interval(self, rr_interval: float) -> Optional[HRVMetrics]:
        """
        Add a new RR interval and calculate HRV if window is full

        Args:
            rr_interval: RR interval in milliseconds

        Returns:
            HRVMetrics if window is full, None otherwise
        """
        self.rr_buffer.append(rr_interval)

        # Keep only the most recent window_size intervals
        if len(self.rr_buffer) > self.window_size:
            self.rr_buffer.pop(0)

        # Calculate HRV if we have enough data
        if len(self.rr_buffer) >= self.window_size:
            return self.calculator.calculate_hrv_metrics(
                rr_intervals=self.rr_buffer.copy(),
                filter_outliers=True
            )

        return None

    def add_heart_rate(self, heart_rate: float) -> Optional[HRVMetrics]:
        """
        Add a new heart rate measurement and calculate HRV if window is full

        Args:
            heart_rate: Heart rate in beats per minute

        Returns:
            HRVMetrics if window is full, None otherwise
        """
        if heart_rate > 0:
            rr_interval = 60000.0 / heart_rate
            return self.add_rr_interval(rr_interval)
        return None

    def get_current_hrv(self) -> Optional[HRVMetrics]:
        """
        Get current HRV metrics without adding new data

        Returns:
            HRVMetrics if sufficient data is available, None otherwise
        """
        if len(self.rr_buffer) >= min(30, self.window_size):
            return self.calculator.calculate_hrv_metrics(
                rr_intervals=self.rr_buffer.copy(),
                filter_outliers=True
            )
        return None

    def reset(self):
        """Reset the buffer"""
        self.rr_buffer.clear()
