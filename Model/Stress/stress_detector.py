"""
Stress Level Detection from HRV

Uses HRV metrics to estimate stress levels based on research-backed thresholds:
- Low HRV → High Stress
- High HRV → Low Stress

References:
- Kim et al. (2018). Stress and Heart Rate Variability: A Meta-Analysis
- Thayer et al. (2012). A meta-analysis of heart rate variability and neuroimaging studies
"""

from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from hrv_calculator import HRVMetrics


class StressLevel(Enum):
    """Stress level categories"""
    VERY_LOW = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    VERY_HIGH = 5

    def __str__(self):
        return self.name.replace('_', ' ').title()

    def to_korean(self) -> str:
        """Korean translation"""
        translations = {
            StressLevel.VERY_LOW: "매우 낮음",
            StressLevel.LOW: "낮음",
            StressLevel.MODERATE: "보통",
            StressLevel.HIGH: "높음",
            StressLevel.VERY_HIGH: "매우 높음"
        }
        return translations[self]


@dataclass
class StressAssessment:
    """Container for stress assessment results"""
    stress_level: StressLevel
    stress_score: float  # 0-100 (0=no stress, 100=extreme stress)
    confidence: float  # 0-1
    hrv_metrics: HRVMetrics
    reasoning: str
    timestamp: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'stress_level': str(self.stress_level),
            'stress_level_value': self.stress_level.value,
            'stress_level_korean': self.stress_level.to_korean(),
            'stress_score': round(self.stress_score, 2),
            'confidence': round(self.confidence, 2),
            'hrv_metrics': self.hrv_metrics.to_dict(),
            'reasoning': self.reasoning,
            'timestamp': self.timestamp.isoformat()
        }


class StressDetector:
    """
    Detects stress levels from HRV metrics
    """

    # HRV thresholds based on research (age-adjusted ranges for adults)
    # These are general guidelines and may vary by individual
    RMSSD_THRESHOLDS = {
        'very_high': 15,   # RMSSD < 15ms → Very High Stress
        'high': 25,        # RMSSD < 25ms → High Stress
        'moderate': 35,    # RMSSD < 35ms → Moderate Stress
        'low': 50,         # RMSSD < 50ms → Low Stress
        # RMSSD >= 50ms → Very Low Stress
    }

    SDNN_THRESHOLDS = {
        'very_high': 30,   # SDNN < 30ms → Very High Stress
        'high': 50,        # SDNN < 50ms → High Stress
        'moderate': 70,    # SDNN < 70ms → Moderate Stress
        'low': 100,        # SDNN < 100ms → Low Stress
        # SDNN >= 100ms → Very Low Stress
    }

    def __init__(self,
                 use_rmssd: bool = True,
                 use_sdnn: bool = True,
                 use_pnn50: bool = True):
        """
        Initialize stress detector

        Args:
            use_rmssd: Use RMSSD for stress detection (default: True)
            use_sdnn: Use SDNN for stress detection (default: True)
            use_pnn50: Use pNN50 for stress detection (default: True)
        """
        self.use_rmssd = use_rmssd
        self.use_sdnn = use_sdnn
        self.use_pnn50 = use_pnn50

    def _assess_rmssd(self, rmssd: float) -> tuple[StressLevel, float]:
        """
        Assess stress level from RMSSD

        Args:
            rmssd: RMSSD value in milliseconds

        Returns:
            Tuple of (StressLevel, stress_score)
        """
        if rmssd < self.RMSSD_THRESHOLDS['very_high']:
            return StressLevel.VERY_HIGH, 90.0
        elif rmssd < self.RMSSD_THRESHOLDS['high']:
            # Linear interpolation between very_high and high
            score = 70 + (self.RMSSD_THRESHOLDS['high'] - rmssd) / \
                   (self.RMSSD_THRESHOLDS['high'] - self.RMSSD_THRESHOLDS['very_high']) * 20
            return StressLevel.HIGH, score
        elif rmssd < self.RMSSD_THRESHOLDS['moderate']:
            score = 50 + (self.RMSSD_THRESHOLDS['moderate'] - rmssd) / \
                   (self.RMSSD_THRESHOLDS['moderate'] - self.RMSSD_THRESHOLDS['high']) * 20
            return StressLevel.MODERATE, score
        elif rmssd < self.RMSSD_THRESHOLDS['low']:
            score = 30 + (self.RMSSD_THRESHOLDS['low'] - rmssd) / \
                   (self.RMSSD_THRESHOLDS['low'] - self.RMSSD_THRESHOLDS['moderate']) * 20
            return StressLevel.LOW, score
        else:
            # Very low stress
            score = max(0, 30 - (rmssd - self.RMSSD_THRESHOLDS['low']) * 0.2)
            return StressLevel.VERY_LOW, score

    def _assess_sdnn(self, sdnn: float) -> tuple[StressLevel, float]:
        """
        Assess stress level from SDNN

        Args:
            sdnn: SDNN value in milliseconds

        Returns:
            Tuple of (StressLevel, stress_score)
        """
        if sdnn < self.SDNN_THRESHOLDS['very_high']:
            return StressLevel.VERY_HIGH, 90.0
        elif sdnn < self.SDNN_THRESHOLDS['high']:
            score = 70 + (self.SDNN_THRESHOLDS['high'] - sdnn) / \
                   (self.SDNN_THRESHOLDS['high'] - self.SDNN_THRESHOLDS['very_high']) * 20
            return StressLevel.HIGH, score
        elif sdnn < self.SDNN_THRESHOLDS['moderate']:
            score = 50 + (self.SDNN_THRESHOLDS['moderate'] - sdnn) / \
                   (self.SDNN_THRESHOLDS['moderate'] - self.SDNN_THRESHOLDS['high']) * 20
            return StressLevel.MODERATE, score
        elif sdnn < self.SDNN_THRESHOLDS['low']:
            score = 30 + (self.SDNN_THRESHOLDS['low'] - sdnn) / \
                   (self.SDNN_THRESHOLDS['low'] - self.SDNN_THRESHOLDS['moderate']) * 20
            return StressLevel.LOW, score
        else:
            score = max(0, 30 - (sdnn - self.SDNN_THRESHOLDS['low']) * 0.15)
            return StressLevel.VERY_LOW, score

    def _assess_pnn50(self, pnn50: float) -> tuple[StressLevel, float]:
        """
        Assess stress level from pNN50

        Args:
            pnn50: pNN50 percentage

        Returns:
            Tuple of (StressLevel, stress_score)
        """
        # pNN50 < 3% indicates high stress
        # pNN50 > 15% indicates low stress
        if pnn50 < 1:
            return StressLevel.VERY_HIGH, 90.0
        elif pnn50 < 3:
            score = 70 + (3 - pnn50) / 2 * 20
            return StressLevel.HIGH, score
        elif pnn50 < 7:
            score = 50 + (7 - pnn50) / 4 * 20
            return StressLevel.MODERATE, score
        elif pnn50 < 15:
            score = 30 + (15 - pnn50) / 8 * 20
            return StressLevel.LOW, score
        else:
            score = max(0, 30 - (pnn50 - 15) * 1.0)
            return StressLevel.VERY_LOW, score

    def detect_stress(self, hrv_metrics: HRVMetrics) -> StressAssessment:
        """
        Detect stress level from HRV metrics

        Args:
            hrv_metrics: HRV metrics to analyze

        Returns:
            StressAssessment with detected stress level and details
        """
        assessments = []
        weights = []
        reasoning_parts = []

        # Assess RMSSD
        if self.use_rmssd and hrv_metrics.rmssd > 0:
            level, score = self._assess_rmssd(hrv_metrics.rmssd)
            assessments.append((level, score))
            weights.append(0.4)  # RMSSD is most reliable for stress
            reasoning_parts.append(
                f"RMSSD: {hrv_metrics.rmssd:.1f}ms → {level}"
            )

        # Assess SDNN
        if self.use_sdnn and hrv_metrics.sdnn > 0:
            level, score = self._assess_sdnn(hrv_metrics.sdnn)
            assessments.append((level, score))
            weights.append(0.35)  # SDNN is also reliable
            reasoning_parts.append(
                f"SDNN: {hrv_metrics.sdnn:.1f}ms → {level}"
            )

        # Assess pNN50
        if self.use_pnn50:
            level, score = self._assess_pnn50(hrv_metrics.pnn50)
            assessments.append((level, score))
            weights.append(0.25)  # pNN50 is supplementary
            reasoning_parts.append(
                f"pNN50: {hrv_metrics.pnn50:.1f}% → {level}"
            )

        # Calculate weighted average stress score
        if not assessments:
            return StressAssessment(
                stress_level=StressLevel.MODERATE,
                stress_score=50.0,
                confidence=0.0,
                hrv_metrics=hrv_metrics,
                reasoning="Insufficient HRV data for assessment",
                timestamp=hrv_metrics.timestamp
            )

        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        # Calculate weighted average stress score
        weighted_score = sum(score * weight
                            for (_, score), weight
                            in zip(assessments, normalized_weights))

        # Determine final stress level from weighted score
        if weighted_score >= 80:
            final_level = StressLevel.VERY_HIGH
        elif weighted_score >= 60:
            final_level = StressLevel.HIGH
        elif weighted_score >= 40:
            final_level = StressLevel.MODERATE
        elif weighted_score >= 20:
            final_level = StressLevel.LOW
        else:
            final_level = StressLevel.VERY_LOW

        # Calculate confidence based on agreement between metrics
        stress_levels = [level.value for level, _ in assessments]
        if len(stress_levels) > 1:
            level_variance = sum((l - sum(stress_levels) / len(stress_levels)) ** 2
                               for l in stress_levels) / len(stress_levels)
            # Lower variance = higher confidence
            confidence = max(0.5, 1.0 - (level_variance / 4.0))
        else:
            confidence = 0.7  # Single metric confidence

        reasoning = "; ".join(reasoning_parts)

        return StressAssessment(
            stress_level=final_level,
            stress_score=weighted_score,
            confidence=confidence,
            hrv_metrics=hrv_metrics,
            reasoning=reasoning,
            timestamp=hrv_metrics.timestamp
        )

    def get_stress_recommendations(self, assessment: StressAssessment) -> Dict[str, list]:
        """
        Get recommendations based on stress assessment

        Args:
            assessment: Stress assessment result

        Returns:
            Dictionary with recommendations in English and Korean
        """
        recommendations_en = {
            StressLevel.VERY_LOW: [
                "Your stress level is very low. Keep up the good work!",
                "Consider maintaining your current healthy habits.",
                "You're in an optimal state for productivity and wellbeing."
            ],
            StressLevel.LOW: [
                "Your stress level is low and healthy.",
                "Continue your current stress management practices.",
                "Maintain regular exercise and good sleep habits."
            ],
            StressLevel.MODERATE: [
                "Your stress level is moderate.",
                "Consider taking short breaks throughout the day.",
                "Practice deep breathing or brief meditation.",
                "Ensure you're getting adequate sleep."
            ],
            StressLevel.HIGH: [
                "Your stress level is elevated.",
                "Take a 10-15 minute break to relax.",
                "Practice deep breathing exercises.",
                "Consider light physical activity like walking.",
                "Avoid caffeine and stimulants."
            ],
            StressLevel.VERY_HIGH: [
                "Your stress level is very high.",
                "Take immediate steps to relax.",
                "Find a quiet place and practice deep breathing for 5-10 minutes.",
                "Consider talking to someone you trust.",
                "If stress persists, consult a healthcare professional."
            ]
        }

        recommendations_ko = {
            StressLevel.VERY_LOW: [
                "스트레스 수준이 매우 낮습니다. 계속 유지하세요!",
                "현재의 건강한 습관을 유지하는 것을 고려하세요.",
                "생산성과 웰빙을 위한 최적의 상태입니다."
            ],
            StressLevel.LOW: [
                "스트레스 수준이 낮고 건강합니다.",
                "현재의 스트레스 관리 방법을 계속 유지하세요.",
                "규칙적인 운동과 좋은 수면 습관을 유지하세요."
            ],
            StressLevel.MODERATE: [
                "스트레스 수준이 보통입니다.",
                "하루 종일 짧은 휴식을 취하는 것을 고려하세요.",
                "심호흡이나 짧은 명상을 실천하세요.",
                "충분한 수면을 취하고 있는지 확인하세요."
            ],
            StressLevel.HIGH: [
                "스트레스 수준이 높습니다.",
                "10-15분 정도 휴식을 취하세요.",
                "심호흡 운동을 실천하세요.",
                "걷기와 같은 가벼운 신체 활동을 고려하세요.",
                "카페인과 자극제를 피하세요."
            ],
            StressLevel.VERY_HIGH: [
                "스트레스 수준이 매우 높습니다.",
                "즉시 긴장을 풀기 위한 조치를 취하세요.",
                "조용한 장소를 찾아 5-10분간 심호흡을 하세요.",
                "신뢰할 수 있는 사람과 대화하는 것을 고려하세요.",
                "스트레스가 지속되면 의료 전문가와 상담하세요."
            ]
        }

        return {
            'english': recommendations_en[assessment.stress_level],
            'korean': recommendations_ko[assessment.stress_level]
        }
