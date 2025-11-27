"""
Feature configuration for fatigue prediction models
"""

# Apple Watch biometric features
BIOMETRIC_FEATURES = [
    'heart_rate_avg',           # 평균 심박수
    'heart_rate_min',           # 최소 심박수
    'heart_rate_max',           # 최대 심박수
    'heart_rate_variability',   # 심박변이도 (HRV)
    'resting_heart_rate',       # 휴식 시 심박수
    'steps',                    # 걸음 수
    'active_calories',          # 활동 칼로리
    'exercise_minutes',         # 운동 시간 (분)
    'stand_hours',              # 서있던 시간
    'sleep_hours',              # 수면 시간
    'sleep_quality',            # 수면 질 (0-100)
    'blood_oxygen',             # 혈중 산소포화도
]

# Weather features (from KMA API or OpenMeteo)
WEATHER_FEATURES = [
    'temperature',              # 온도
    'humidity',                 # 습도
    'precipitation',            # 강수량
    'wind_speed',              # 풍속
    'atmospheric_pressure',     # 기압
    'uv_index',                # 자외선 지수
]

# Weather feature names with time offset
def get_weather_features_with_offset():
    features = []
    for offset in [0, 1, 3, 7]:  # 당일, 1일전, 3일전, 7일전
        for feature in WEATHER_FEATURES:
            features.append(f'{feature}_d{offset}')
    return features

# All features
ALL_FEATURES = BIOMETRIC_FEATURES + get_weather_features_with_offset()

# Target variable (3 classes)
TARGET_CLASSES = ['좋음', '보통', '나쁨']  # Good, Normal, Bad
TARGET_CLASS_MAPPING = {
    '좋음': 0,
    '보통': 1,
    '나쁨': 2
}

# User types
USER_TYPES = ['student', 'worker', 'general']
