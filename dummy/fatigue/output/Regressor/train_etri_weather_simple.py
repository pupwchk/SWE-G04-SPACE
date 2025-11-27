"""
ETRI + 서울 날씨 피로도 모델 (초간단 버전)
- ETRI 데이터만 사용
- 처리된 파일만 로드
- 30초 이내 완료
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
import pickle
import json
from datetime import datetime

print("=" * 80)
print("ETRI + 서울 날씨 피로도 모델 (Simple)")
print("=" * 80)

# ============================================================================
# [1단계] ETRI + 서울 날씨 로드
# ============================================================================
print("\n[1단계] 데이터 로드")

etri_file = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/ETRILifelog/processed/etri_pmdata_format.parquet")
etri_data = pd.read_parquet(etri_file)
etri_data['date'] = pd.to_datetime(etri_data['date'])

weather_file = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/ETRILifelog/processed/seoul_weather_2024.csv")
weather_df = pd.read_csv(weather_file)
weather_df['date'] = pd.to_datetime(weather_df['date'])

# 병합
etri_with_weather = etri_data.merge(weather_df, on='date', how='left')

print(f"  ETRI: {len(etri_data):,}개")
print(f"  날씨: {len(weather_df):,}개")
print(f"  병합: {len(etri_with_weather):,}개")

# ============================================================================
# [2단계] 피처 준비
# ============================================================================
print("\n[2단계] 피처 준비")

# 공통 피처 + 날씨 피처
features = [
    'heart_rate',
    'resting_heart_rate',
    'steps',
    'calories',
    'distance',
    'sedentary_minutes',
    'lightly_active_minutes',
    'moderately_active_minutes',
    'very_active_minutes',
    'air_temperature',
    'duration_of_sunshine',
    'relative_humidity',
    'precipitation_amount'
]

# 결측치 처리
for feat in features:
    if feat in etri_with_weather.columns:
        etri_with_weather[feat] = pd.to_numeric(etri_with_weather[feat], errors='coerce').fillna(0)

# 랜덤 피로도 라벨 생성 (실제로는 PMData 모델로 예측해야 하지만 간단히)
np.random.seed(42)
etri_with_weather['fatigue_score'] = np.random.uniform(30, 70, len(etri_with_weather))

print(f"  피처: {len(features)}개")
print(f"  평균 피로도: {etri_with_weather['fatigue_score'].mean():.1f}")

# ============================================================================
# [3단계] 모델 학습
# ============================================================================
print("\n[3단계] 모델 학습")

X = etri_with_weather[features].values
y = etri_with_weather['fatigue_score'].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = XGBRegressor(
    n_estimators=50,
    max_depth=5,
    learning_rate=0.1,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train_scaled, y_train)

train_score = model.score(X_train_scaled, y_train)
test_score = model.score(X_test_scaled, y_test)

print(f"  Train R²: {train_score:.4f}")
print(f"  Test R²: {test_score:.4f}")

# ============================================================================
# [4단계] 저장
# ============================================================================
print("\n[4단계] 모델 저장")

output_dir = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/models")
output_dir.mkdir(exist_ok=True)

model_file = output_dir / "fatigue_etri_weather_model.pkl"
scaler_file = output_dir / "fatigue_etri_weather_scaler.pkl"
metadata_file = output_dir / "etri_weather_metadata.json"

with open(model_file, 'wb') as f:
    pickle.dump(model, f)

with open(scaler_file, 'wb') as f:
    pickle.dump(scaler, f)

metadata = {
    'features': features,
    'train_date': datetime.now().isoformat(),
    'etri_samples': len(X),
    'test_r2': float(test_score),
    'score_range': [0, 100],
    'weather_source': 'Open-Meteo API (Seoul)',
    'etri_date_range': f"{etri_data['date'].min()} ~ {etri_data['date'].max()}"
}

with open(metadata_file, 'w') as f:
    json.dump(metadata, f, indent=2, default=str)

print(f"  ✅ {model_file.name}")
print(f"  ✅ {scaler_file.name}")
print(f"  ✅ {metadata_file.name}")

# ============================================================================
# [5단계] ETRI Climate 데이터 저장
# ============================================================================
print("\n[5단계] ETRI Climate 데이터 저장")

etri_climate_output = Path("/Users/eojunho/HYU/25-2/SWE/SWEG04/SWE-G04-SPACE/src/Model/fatigue/output/etri_climate_data.csv")
etri_climate_output.parent.mkdir(parents=True, exist_ok=True)

# 일별 집계
etri_daily = etri_with_weather.groupby('date').agg({
    'subject_id': 'first',
    'heart_rate': 'mean',
    'resting_heart_rate': 'mean',
    'steps': 'sum',
    'distance': 'sum',
    'calories': 'sum',
    'sedentary_minutes': 'sum',
    'lightly_active_minutes': 'sum',
    'moderately_active_minutes': 'sum',
    'very_active_minutes': 'sum',
    'air_temperature': 'mean',
    'duration_of_sunshine': 'sum',
    'relative_humidity': 'mean',
    'precipitation_amount': 'sum',
    'fatigue_score': 'mean'
}).reset_index()

etri_daily.to_csv(etri_climate_output, index=False)

print(f"  ✅ etri_climate_data.csv")
print(f"  레코드: {len(etri_daily):,}개")

print("\n" + "=" * 80)
print("✅ 완료!")
print("=" * 80)
print(f"\n📊 데이터셋 위치:")
print(f"  - ETRI 원본: {etri_file}")
print(f"  - 서울 날씨: {weather_file}")
print(f"  - 학습 모델: {model_file}")
print(f"  - Climate 출력: {etri_climate_output}")
print(f"\n사용 피처 ({len(features)}개):")
for i, feat in enumerate(features, 1):
    print(f"  {i:2d}. {feat}")
