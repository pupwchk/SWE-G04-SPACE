"""
기존 XGBoost JSON 모델을 pkl 형식으로 변환 및 저장
scikit-learn 호환 형식으로 재학습하여 저장
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
import pickle
import json
import sys
import os

# Add config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.features_config import (
    BIOMETRIC_FEATURES,
    get_weather_features_with_offset,
    USER_TYPES
)


def load_data(data_path):
    """데이터 로드"""
    df = pd.read_csv(data_path)
    feature_columns = BIOMETRIC_FEATURES + get_weather_features_with_offset()
    X = df[feature_columns].values
    y = df['fatigue_label'].values
    return X, y


def train_and_save_sklearn_xgboost(user_type, data_path, output_dir):
    """
    scikit-learn 호환 XGBoost 모델 학습 및 pkl 저장

    Args:
        user_type: 'student', 'worker', or 'general'
        data_path: 데이터 경로
        output_dir: 저장 디렉토리
    """
    print(f"\n{'='*70}")
    print(f"Converting {user_type.upper()} model to pkl format")
    print('='*70)

    # 데이터 로드
    print(f"Loading data from {data_path}...")
    X, y = load_data(data_path)

    # 데이터 분할 (기존 모델과 동일하게)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print(f"Train samples: {len(X_train)}, Test samples: {len(X_test)}")

    # 기존 모델의 파라미터 로드
    metadata_path = os.path.join(output_dir, f'{user_type}_metadata.json')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            params = metadata.get('params', {})
        print(f"Loaded parameters from metadata")
    else:
        # 기본 파라미터
        params = {
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 3,
            'gamma': 0.1,
            'random_state': 42
        }
        print(f"Using default parameters")

    # scikit-learn 호환 XGBoost 모델 생성
    print("\nTraining XGBClassifier...")
    model = xgb.XGBClassifier(
        objective='multi:softprob',
        num_class=3,
        max_depth=params.get('max_depth', 6),
        learning_rate=params.get('learning_rate', 0.1),
        n_estimators=params.get('n_estimators', 100),
        subsample=params.get('subsample', 0.8),
        colsample_bytree=params.get('colsample_bytree', 0.8),
        min_child_weight=params.get('min_child_weight', 3),
        gamma=params.get('gamma', 0.1),
        random_state=params.get('random_state', 42),
        eval_metric='mlogloss',
        use_label_encoder=False
    )

    # 모델 학습
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )

    # 평가
    from sklearn.metrics import accuracy_score, f1_score
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average='macro')
    f1_weighted = f1_score(y_test, y_pred, average='weighted')

    print(f"\nModel Performance:")
    print(f"  Accuracy: {accuracy:.4f}")
    print(f"  F1 (Macro): {f1_macro:.4f}")
    print(f"  F1 (Weighted): {f1_weighted:.4f}")

    # pkl 파일로 저장
    pkl_path = os.path.join(output_dir, f'{user_type}_xgboost_model.pkl')
    with open(pkl_path, 'wb') as f:
        pickle.dump(model, f)

    print(f"\n✓ Model saved to {pkl_path}")

    # 파일 크기 확인
    file_size = os.path.getsize(pkl_path)
    print(f"  File size: {file_size / 1024:.1f} KB")

    return model, pkl_path


def verify_pkl_model(pkl_path, data_path):
    """저장된 pkl 모델 검증"""
    print(f"\nVerifying model at {pkl_path}...")

    # 모델 로드
    with open(pkl_path, 'rb') as f:
        loaded_model = pickle.load(f)

    # 데이터 로드
    X, y = load_data(data_path)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 예측 테스트
    predictions = loaded_model.predict(X_test[:5])
    probabilities = loaded_model.predict_proba(X_test[:5])

    print("✓ Model loaded successfully")
    print(f"  Sample predictions: {predictions}")
    print(f"  Sample probabilities shape: {probabilities.shape}")

    return True


def main():
    """메인 함수"""
    print("="*70)
    print("Converting XGBoost JSON models to pkl format")
    print("="*70)

    script_dir = os.path.dirname(__file__)
    data_dir = os.path.join(script_dir, '..', 'data')
    models_dir = os.path.join(script_dir, '..', 'models')

    os.makedirs(models_dir, exist_ok=True)

    results = {}

    for user_type in USER_TYPES:
        data_path = os.path.join(data_dir, f'{user_type}_data.csv')

        if not os.path.exists(data_path):
            print(f"Warning: Data file not found for {user_type}")
            continue

        # 모델 학습 및 pkl 저장
        model, pkl_path = train_and_save_sklearn_xgboost(
            user_type,
            data_path,
            models_dir
        )

        # 검증
        verify_pkl_model(pkl_path, data_path)

        results[user_type] = pkl_path

    print("\n" + "="*70)
    print("Conversion Summary")
    print("="*70)

    for user_type, pkl_path in results.items():
        print(f"✓ {user_type.upper()}: {pkl_path}")

    print("\n" + "="*70)
    print("All models converted to pkl format successfully!")
    print("="*70)

    # 사용 예제 출력
    print("\n" + "="*70)
    print("Usage Example")
    print("="*70)
    print("""
import pickle
import numpy as np

# 모델 로드
with open('models/student_xgboost_model.pkl', 'rb') as f:
    model = pickle.load(f)

# 예측
predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)

# 단일 샘플 예측
single_prediction = model.predict([features])
single_proba = model.predict_proba([features])
""")


if __name__ == '__main__':
    main()
