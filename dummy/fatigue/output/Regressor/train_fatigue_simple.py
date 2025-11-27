"""
간단 버전: Wellness 데이터만 사용한 피로도 예측 모델
PMData의 wellness 피처 + ETRI의 공통 피처로 학습
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
import pickle
import json

print("=" * 80)
print("피로도 예측 모델 - 간단 버전")
print("=" * 80)

# PMData wellness 데이터 로드
print("\n[1] PMData Wellness 데이터 로드")
pm_dir = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/pmdata")

wellness_data = []
for p_dir in pm_dir.glob("p*/pmsys/wellness.csv"):
    df = pd.read_csv(p_dir)
    df['participant'] = p_dir.parent.parent.name
    wellness_data.append(df)

pm_wellness = pd.concat(wellness_data, ignore_index=True)
print(f"  레코드: {len(pm_wellness):,}개")
print(f"  컬럼: {pm_wellness.columns.tolist()}")

# 피로도 라벨 → 0~100 점수 변환
def label_to_score(label):
    if pd.isna(label):
        return np.nan
    label = int(label)
    ranges = {0: (0,10), 1: (10, 30), 2: (30, 50), 3: (50, 70), 4: (70, 90), 5: (90, 100)}
    if label in ranges:
        low, high = ranges[label]
        return np.random.uniform(low, high)
    return np.nan

pm_wellness['fatigue_score'] = pm_wellness['fatigue'].apply(label_to_score)
pm_wellness = pm_wellness[pm_wellness['fatigue_score'].notna()]

print(f"  유효 레코드: {len(pm_wellness):,}개")
print(f"  피로도 분포: {pm_wellness['fatigue'].value_counts().sort_index().to_dict()}")

# PMData 피처 (wellness만)
pm_features = ['sleep_duration_h', 'sleep_quality', 'soreness', 'stress', 'mood', 'readiness']
X_pm = pm_wellness[pm_features].fillna(pm_wellness[pm_features].mean()).values
y_pm = pm_wellness['fatigue_score'].values

print(f"\n[2] PMData 모델 학습")
X_train, X_test, y_train, y_test = train_test_split(X_pm, y_pm, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
model.fit(X_train_scaled, y_train)

train_r2 = model.score(X_train_scaled, y_train)
test_r2 = model.score(X_test_scaled, y_test)
print(f"  Train R²: {train_r2:.4f}")
print(f"  Test R²: {test_r2:.4f}")

# ETRI 데이터로 확장 (간단히 랜덤으로 생성 - 실제로는 공통 피처 사용)
print(f"\n[3] ETRI Pseudo-labeling (데모)")
etri = pd.read_parquet("/Users/eojunho/HYU/25-2/SWE/lifelog/ETRILifelog/processed/etri_pmdata_format.parquet")

# ETRI에는 wellness 피처가 없으므로, 건강 피처로부터 유추
# 간단한 매핑: 심박수/활동량 → wellness 피처 추정
etri['sleep_duration_h'] = np.clip(7 - (etri['heart_rate'] - 70) / 10, 4, 10)  # 추정
etri['sleep_quality'] = np.random.uniform(2, 4, len(etri))  # 추정
etri['soreness'] = np.clip(etri['very_active_minutes'] / 10, 0, 5)  # 추정
etri['stress'] = np.clip((100 - etri['heart_rate']) / 20, 0, 5)  # 추정
etri['mood'] = np.random.uniform(2, 4, len(etri))  # 추정
etri['readiness'] = np.clip(5 - etri['stress'], 0, 5)  # 추정

X_etri = etri[pm_features].fillna(etri[pm_features].mean()).values
X_etri_scaled = scaler.transform(X_etri)
etri['fatigue_pseudo'] = model.predict(X_etri_scaled).clip(0, 100)

print(f"  ETRI 레코드: {len(etri):,}개")
print(f"  Pseudo-label 평균: {etri['fatigue_pseudo'].mean():.1f}")

# Incremental Learning
print(f"\n[4] Incremental Learning")
X_combined = np.vstack([X_train_scaled, X_etri_scaled])
y_combined = np.concatenate([y_train, etri['fatigue_pseudo'].values])

final_model = XGBRegressor(n_estimators=50, max_depth=5, learning_rate=0.05, random_state=42)
final_model.fit(X_combined, y_combined, xgb_model=model.get_booster())

final_r2 = final_model.score(X_test_scaled, y_test)
print(f"  Final R²: {final_r2:.4f} (Before: {test_r2:.4f})")

# 저장
print(f"\n[5] 모델 저장")
output_dir = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/models")
output_dir.mkdir(exist_ok=True)

with open(output_dir / "fatigue_model.pkl", 'wb') as f:
    pickle.dump(final_model, f)
with open(output_dir / "fatigue_scaler.pkl", 'wb') as f:
    pickle.dump(scaler, f)

metadata = {'features': pm_features, 'score_range': [0, 100], 'test_r2': float(final_r2)}
with open(output_dir / "model_metadata.json", 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"  ✅ 저장 완료")
print("\n" + "=" * 80)
print("완료!")
