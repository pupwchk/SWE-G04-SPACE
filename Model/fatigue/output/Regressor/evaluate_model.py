"""
피로도 예측 모델 성능 평가
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt

print("=" * 80)
print("피로도 예측 모델 평가")
print("=" * 80)

# 모델 로드
model_dir = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/models")
model_file = model_dir / "fatigue_etri_weather_model.pkl"
scaler_file = model_dir / "fatigue_etri_weather_scaler.pkl"
metadata_file = model_dir / "etri_weather_metadata.json"

with open(model_file, 'rb') as f:
    model = pickle.load(f)

with open(scaler_file, 'rb') as f:
    scaler = pickle.load(f)

import json
with open(metadata_file, 'r') as f:
    metadata = json.load(f)

print("\n[모델 정보]")
print(f"  학습 날짜: {metadata.get('train_date', 'N/A')}")
print(f"  ETRI 샘플: {metadata.get('etri_samples', 'N/A'):,}개")
print(f"  Test R²: {metadata.get('test_r2', 'N/A'):.4f}")
print(f"  피처 수: {len(metadata.get('features', []))}개")

# 테스트 데이터 로드
print("\n[테스트 데이터 로드]")
etri_file = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/ETRILifelog/processed/etri_pmdata_format.parquet")
weather_file = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/ETRILifelog/processed/seoul_weather_2024.csv")

etri_data = pd.read_parquet(etri_file)
etri_data['date'] = pd.to_datetime(etri_data['date'])

weather_df = pd.read_csv(weather_file)
weather_df['date'] = pd.to_datetime(weather_df['date'])

etri_with_weather = etri_data.merge(weather_df, on='date', how='left')

# 피처 준비
features = metadata['features']
for feat in features:
    if feat in etri_with_weather.columns:
        etri_with_weather[feat] = pd.to_numeric(etri_with_weather[feat], errors='coerce').fillna(0)

# 예측
X = etri_with_weather[features].values
X_scaled = scaler.transform(X)

predictions = model.predict(X_scaled)
etri_with_weather['predicted_fatigue'] = predictions.clip(0, 100)

print(f"  예측 완료: {len(predictions):,}개")

# 통계
print("\n[예측 결과 통계]")
print(f"  평균: {predictions.mean():.1f}")
print(f"  표준편차: {predictions.std():.1f}")
print(f"  최소: {predictions.min():.1f}")
print(f"  최대: {predictions.max():.1f}")
print(f"  중앙값: {np.median(predictions):.1f}")

# 분포 확인
bins = [0, 20, 40, 60, 80, 100]
labels = ['매우 낮음(0-20)', '낮음(20-40)', '보통(40-60)', '높음(60-80)', '매우 높음(80-100)']
etri_with_weather['fatigue_category'] = pd.cut(predictions, bins=bins, labels=labels, include_lowest=True)

print("\n[피로도 분포]")
print(etri_with_weather['fatigue_category'].value_counts().sort_index())

# 날짜별 평균
print("\n[일별 평균 피로도 (최근 10일)]")
daily_avg = etri_with_weather.groupby('date')['predicted_fatigue'].mean().sort_index()
print(daily_avg.tail(10))

# 피처 중요도
print("\n[피처 중요도 Top 10]")
feature_importance = model.feature_importances_
importance_df = pd.DataFrame({
    'feature': features,
    'importance': feature_importance
}).sort_values('importance', ascending=False)

for idx, row in importance_df.head(10).iterrows():
    print(f"  {row['feature']:30s}: {row['importance']:.4f}")

# 저장
output_file = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/models/evaluation_results.csv")
etri_with_weather[['date', 'subject_id', 'predicted_fatigue', 'fatigue_category']].to_csv(output_file, index=False)

print(f"\n✅ 평가 결과 저장: {output_file}")

print("\n" + "=" * 80)
print("평가 완료!")
print("=" * 80)
