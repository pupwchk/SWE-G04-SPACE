"""
Fatigue Prediction Service
XGBoost 모델을 로드하여 피로도 예측 수행
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import os

# Fatigue 모델 경로 추가
fatigue_model_path = os.path.join(os.path.dirname(__file__), '../../../../Model/Fatigue')
sys.path.insert(0, fatigue_model_path)

import config


class FatiguePredictionResult:
    """피로도 예측 결과"""
    def __init__(
        self,
        fatigue_level: str,
        fatigue_class: int,
        confidence: float,
        timestamp: datetime,
        feature_values: Dict[str, float]
    ):
        self.fatigue_level = fatigue_level  # "Low", "Medium", "High"
        self.fatigue_class = fatigue_class  # 0, 1, 2
        self.confidence = confidence
        self.timestamp = timestamp
        self.feature_values = feature_values

    def to_dict(self) -> dict:
        return {
            "fatigue_level": self.fatigue_level,
            "fatigue_class": self.fatigue_class,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "feature_values": self.feature_values
        }


class FatiguePredictor:
    """피로도 예측 서비스"""

    def __init__(self, model_path: Optional[Path] = None):
        """
        Args:
            model_path: 모델 파일 경로 (기본값: config.MODEL_DIR / "xgboost_best_model.pkl")
        """
        if model_path is None:
            model_path = config.MODEL_DIR / "xgboost_best_model.pkl"

        self.model_path = model_path
        self.model = None
        self.feature_importance = None
        self._load_model()
        self._load_feature_importance()

    def _load_model(self):
        """학습된 모델 로드"""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            print(f"✓ Loaded fatigue model from {self.model_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}")

    def _load_feature_importance(self):
        """피처 중요도 로드"""
        try:
            importance_file = config.RESULTS_DIR / "feature_importance.csv"
            self.feature_importance = pd.read_csv(importance_file)
            print(f"✓ Loaded feature importance from {importance_file}")
        except Exception as e:
            print(f"⚠️  Failed to load feature importance: {str(e)}")
            self.feature_importance = None

    def _calculate_derived_features(self, data: Dict[str, float]) -> Dict[str, float]:
        """파생 피처 계산 (2_feature_engineering.py의 로직 일부)"""
        derived = data.copy()

        # 1. Sleep efficiency
        if data.get('sleep_time_in_bed', 0) > 0:
            derived['sleep_efficiency'] = data.get('sleep_duration', 0) / data['sleep_time_in_bed']
        else:
            derived['sleep_efficiency'] = 0

        # 2. Sleep quality score
        total_sleep = data.get('sleep_deep', 0) + data.get('sleep_light', 0) + data.get('sleep_rem', 0)
        if total_sleep > 0:
            derived['sleep_quality_score'] = (data.get('sleep_deep', 0) + data.get('sleep_rem', 0)) / total_sleep
            derived['sleep_deep_ratio'] = data.get('sleep_deep', 0) / total_sleep
            derived['sleep_rem_ratio'] = data.get('sleep_rem', 0) / total_sleep
        else:
            derived['sleep_quality_score'] = 0
            derived['sleep_deep_ratio'] = 0
            derived['sleep_rem_ratio'] = 0

        # 3. Exercise-sleep ratio
        if data.get('sleep_duration', 0) > 0:
            derived['exercise_sleep_ratio'] = data.get('exercise_duration', 0) / data['sleep_duration']
        else:
            derived['exercise_sleep_ratio'] = 0

        # 4. Heart rate features
        derived['hr_range'] = data.get('hr_max', 0) - data.get('hr_min', 0)
        if data.get('hr_mean', 0) > 0:
            derived['hr_resting_ratio'] = data.get('resting_hr', 0) / data['hr_mean']
        else:
            derived['hr_resting_ratio'] = 0

        # 5. Activity efficiency
        if data.get('total_steps', 0) > 0:
            derived['calories_per_step'] = data.get('total_calories', 0) / data['total_steps']
            derived['distance_per_step'] = data.get('total_distance', 0) / data['total_steps']
        else:
            derived['calories_per_step'] = 0
            derived['distance_per_step'] = 0

        # 6. Exercise intensity
        if data.get('exercise_duration', 0) > 0:
            derived['exercise_intensity'] = data.get('exercise_calories', 0) / data['exercise_duration']
        else:
            derived['exercise_intensity'] = 0

        # 7. Weather derived features (if available)
        if 'air_temperature' in data and 'relative_humidity' in data:
            derived['feels_like_temp'] = data['air_temperature'] - (data['relative_humidity'] / 100) * 2

        if 'precipitation_amount' in data:
            derived['is_rainy'] = 1 if data['precipitation_amount'] > 0 else 0

        if 'cloud_area_fraction' in data:
            derived['clearness'] = 10 - data['cloud_area_fraction']

        return derived

    def _prepare_features(
        self,
        current_data: Dict[str, float],
        historical_data: Optional[List[Dict[str, float]]] = None
    ) -> np.ndarray:
        """
        모델 입력 피처 준비

        Args:
            current_data: 당일 데이터 (HealthKit + WeatherKit)
            historical_data: 과거 7일 데이터 (rolling average 계산용)

        Returns:
            모델 입력 피처 배열
        """
        # 파생 피처 계산
        features = self._calculate_derived_features(current_data)

        # Rolling average 계산 (7일, 3일)
        if historical_data and len(historical_data) >= 3:
            df = pd.DataFrame(historical_data + [features])

            rolling_columns = [
                'total_steps', 'total_calories', 'total_distance',
                'resting_hr', 'hr_mean', 'hr_std',
                'sleep_duration', 'sleep_deep', 'sleep_rem',
                'exercise_duration'
            ]

            # 날씨 피처 추가 (있을 경우)
            weather_columns = ['air_temperature', 'relative_humidity', 'air_pressure_at_sea_level']
            for col in weather_columns:
                if col in features:
                    rolling_columns.append(col)

            # 7일 평균
            for col in rolling_columns:
                if col in df.columns:
                    features[f'{col}_7d_avg'] = df[col].tail(7).mean()
                    features[f'{col}_3d_avg'] = df[col].tail(3).mean()
                else:
                    features[f'{col}_7d_avg'] = 0
                    features[f'{col}_3d_avg'] = 0

            # Diff 피처 (전날 대비)
            diff_columns = ['total_steps', 'resting_hr', 'sleep_duration', 'hr_mean']
            if len(historical_data) >= 1:
                prev_day = historical_data[-1]
                for col in diff_columns:
                    if col in features and col in prev_day:
                        features[f'{col}_diff_1d'] = features[col] - prev_day[col]
                    else:
                        features[f'{col}_diff_1d'] = 0
        else:
            # 과거 데이터 없으면 0으로 채움
            rolling_columns = [
                'total_steps', 'total_calories', 'total_distance',
                'resting_hr', 'hr_mean', 'hr_std',
                'sleep_duration', 'sleep_deep', 'sleep_rem',
                'exercise_duration',
                'air_temperature', 'relative_humidity', 'air_pressure_at_sea_level'
            ]
            for col in rolling_columns:
                features[f'{col}_7d_avg'] = 0
                features[f'{col}_3d_avg'] = 0

            diff_columns = ['total_steps', 'resting_hr', 'sleep_duration', 'hr_mean']
            for col in diff_columns:
                features[f'{col}_diff_1d'] = 0

        # Temporal features
        timestamp = current_data.get('timestamp', datetime.now())
        features['day_of_week'] = timestamp.weekday()
        features['is_weekend'] = 1 if timestamp.weekday() >= 5 else 0
        features['day_of_month'] = timestamp.day
        features['week_of_year'] = timestamp.isocalendar()[1]

        # 모델이 기대하는 피처 순서대로 정렬 (feature_list.txt 기준)
        # 제외: participant, participant_encoded, date, fatigue, mood, stress, sleep_quality, soreness
        expected_features = [
            'air_pressure_at_sea_level', 'air_pressure_at_sea_level_3d_avg', 'air_pressure_at_sea_level_7d_avg',
            'air_temperature', 'air_temperature_3d_avg', 'air_temperature_7d_avg',
            'calories_per_step', 'clearness', 'cloud_area_fraction',
            'day_of_month', 'day_of_week',
            'distance_per_step', 'duration_of_sunshine',
            'exercise_calories', 'exercise_count', 'exercise_duration',
            'exercise_duration_3d_avg', 'exercise_duration_7d_avg',
            'exercise_intensity', 'exercise_sleep_ratio',
            'feels_like_temp',
            'hr_max', 'hr_mean', 'hr_mean_3d_avg', 'hr_mean_7d_avg', 'hr_mean_diff_1d',
            'hr_min', 'hr_range', 'hr_resting_ratio', 'hr_std', 'hr_std_3d_avg', 'hr_std_7d_avg',
            'is_rainy', 'is_weekend',
            'precipitation_amount',
            'relative_humidity', 'relative_humidity_3d_avg', 'relative_humidity_7d_avg',
            'resting_hr', 'resting_hr_3d_avg', 'resting_hr_7d_avg', 'resting_hr_diff_1d',
            'sleep_deep', 'sleep_deep_3d_avg', 'sleep_deep_7d_avg', 'sleep_deep_ratio',
            'sleep_duration', 'sleep_duration_3d_avg', 'sleep_duration_7d_avg', 'sleep_duration_diff_1d',
            'sleep_efficiency', 'sleep_light',
            'sleep_quality_score',
            'sleep_rem', 'sleep_rem_3d_avg', 'sleep_rem_7d_avg', 'sleep_rem_ratio',
            'sleep_time_in_bed', 'sleep_wake',
            'total_calories', 'total_calories_3d_avg', 'total_calories_7d_avg',
            'total_distance', 'total_distance_3d_avg', 'total_distance_7d_avg',
            'total_steps', 'total_steps_3d_avg', 'total_steps_7d_avg', 'total_steps_diff_1d',
            'week_of_year'
        ]

        # 피처 값 추출 (없으면 0)
        feature_vector = [features.get(feat, 0) for feat in expected_features]

        return np.array(feature_vector).reshape(1, -1)

    def predict(
        self,
        current_data: Dict[str, float],
        historical_data: Optional[List[Dict[str, float]]] = None,
        user_normalization: Optional[Dict[str, Dict[str, float]]] = None
    ) -> FatiguePredictionResult:
        """
        피로도 예측

        Args:
            current_data: 당일 건강 데이터 (HealthKit + WeatherKit)
            historical_data: 과거 7일 데이터 (rolling average용)
            user_normalization: 사용자별 정규화 파라미터 {"feature_name": {"mean": x, "std": y}}

        Returns:
            FatiguePredictionResult 객체
        """
        # 피처 준비
        X = self._prepare_features(current_data, historical_data)

        # 개인별 정규화 적용 (있을 경우)
        if user_normalization:
            for i, feat in enumerate(self._get_expected_features()):
                if feat in user_normalization:
                    mean = user_normalization[feat]['mean']
                    std = user_normalization[feat]['std']
                    if std > 1e-6:
                        X[0, i] = (X[0, i] - mean) / std
                    else:
                        X[0, i] = 0

        # 예측
        y_pred = self.model.predict(X)[0]  # 0, 1, 2
        y_proba = self.model.predict_proba(X)[0]  # [p0, p1, p2]

        # 결과 생성
        fatigue_level = config.CLASS_NAMES[y_pred]
        confidence = float(y_proba[y_pred])  # 예측한 클래스의 확률

        return FatiguePredictionResult(
            fatigue_level=fatigue_level,
            fatigue_class=int(y_pred),
            confidence=confidence,
            timestamp=current_data.get('timestamp', datetime.now()),
            feature_values={
                "predicted_class": int(y_pred),
                "class_probabilities": {
                    "Low": float(y_proba[0]),
                    "Medium": float(y_proba[1]),
                    "High": float(y_proba[2])
                }
            }
        )

    def _get_expected_features(self) -> List[str]:
        """모델이 기대하는 피처 목록"""
        return [
            'air_pressure_at_sea_level', 'air_pressure_at_sea_level_3d_avg', 'air_pressure_at_sea_level_7d_avg',
            'air_temperature', 'air_temperature_3d_avg', 'air_temperature_7d_avg',
            'calories_per_step', 'clearness', 'cloud_area_fraction',
            'day_of_month', 'day_of_week',
            'distance_per_step', 'duration_of_sunshine',
            'exercise_calories', 'exercise_count', 'exercise_duration',
            'exercise_duration_3d_avg', 'exercise_duration_7d_avg',
            'exercise_intensity', 'exercise_sleep_ratio',
            'feels_like_temp',
            'hr_max', 'hr_mean', 'hr_mean_3d_avg', 'hr_mean_7d_avg', 'hr_mean_diff_1d',
            'hr_min', 'hr_range', 'hr_resting_ratio', 'hr_std', 'hr_std_3d_avg', 'hr_std_7d_avg',
            'is_rainy', 'is_weekend',
            'precipitation_amount',
            'relative_humidity', 'relative_humidity_3d_avg', 'relative_humidity_7d_avg',
            'resting_hr', 'resting_hr_3d_avg', 'resting_hr_7d_avg', 'resting_hr_diff_1d',
            'sleep_deep', 'sleep_deep_3d_avg', 'sleep_deep_7d_avg', 'sleep_deep_ratio',
            'sleep_duration', 'sleep_duration_3d_avg', 'sleep_duration_7d_avg', 'sleep_duration_diff_1d',
            'sleep_efficiency', 'sleep_light',
            'sleep_quality_score',
            'sleep_rem', 'sleep_rem_3d_avg', 'sleep_rem_7d_avg', 'sleep_rem_ratio',
            'sleep_time_in_bed', 'sleep_wake',
            'total_calories', 'total_calories_3d_avg', 'total_calories_7d_avg',
            'total_distance', 'total_distance_3d_avg', 'total_distance_7d_avg',
            'total_steps', 'total_steps_3d_avg', 'total_steps_7d_avg', 'total_steps_diff_1d',
            'week_of_year'
        ]

    def get_feature_importance(self, top_n: int = 20) -> List[Dict[str, float]]:
        """
        피처 중요도 조회

        Args:
            top_n: 상위 N개 피처

        Returns:
            [{"feature": "name", "importance": 0.123}, ...]
        """
        if self.feature_importance is None:
            return []

        return self.feature_importance.head(top_n).to_dict('records')

    def get_recommendations(self, result: FatiguePredictionResult) -> Dict[str, List[str]]:
        """
        피로도 수준에 따른 권장사항

        Args:
            result: 예측 결과

        Returns:
            {"korean": [...], "english": [...]}
        """
        recommendations = {
            "Low": {
                "korean": [
                    "현재 피로도가 낮습니다. 활동적인 하루를 보내세요!",
                    "충분한 운동과 활동을 유지하세요",
                    "규칙적인 수면 패턴을 유지하세요"
                ],
                "english": [
                    "Your fatigue level is low. Have an active day!",
                    "Maintain sufficient exercise and activity",
                    "Keep a regular sleep pattern"
                ]
            },
            "Medium": {
                "korean": [
                    "중간 수준의 피로도입니다. 무리하지 마세요",
                    "충분한 휴식을 취하고 수면 시간을 확보하세요",
                    "가벼운 스트레칭이나 산책을 권장합니다",
                    "카페인 섭취를 줄이고 수분을 충분히 섭취하세요"
                ],
                "english": [
                    "Your fatigue level is moderate. Don't overdo it",
                    "Get enough rest and ensure adequate sleep",
                    "Light stretching or walking is recommended",
                    "Reduce caffeine intake and stay hydrated"
                ]
            },
            "High": {
                "korean": [
                    "⚠️ 높은 피로도가 감지되었습니다",
                    "충분한 휴식이 필요합니다. 오늘은 일찍 취침하세요",
                    "격렬한 운동을 피하고 가벼운 활동만 하세요",
                    "스트레스 관리와 명상을 권장합니다",
                    "증상이 지속되면 전문가와 상담하세요"
                ],
                "english": [
                    "⚠️ High fatigue level detected",
                    "You need sufficient rest. Go to bed early today",
                    "Avoid intense exercise, only light activities",
                    "Practice stress management and meditation",
                    "Consult a professional if symptoms persist"
                ]
            }
        }

        return recommendations.get(result.fatigue_level, recommendations["Medium"])
