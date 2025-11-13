"""
Step 3: Train XGBoost with RandomizedSearchCV
- Leave-One-Participant-Out Cross Validation
- RandomizedSearch for hyperparameter tuning
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.model_selection import RandomizedSearchCV, LeaveOneGroupOut
from sklearn.metrics import classification_report, f1_score, accuracy_score
from scipy.stats import uniform, randint
import xgboost as xgb
import time

import config
from utils import load_dataframe, print_data_summary


def prepare_data(df: pd.DataFrame):
    """데이터 준비: X, y, groups 분리"""
    print(f"\n{'='*60}")
    print(f"Preparing data...")
    print(f"{'='*60}")

    # Fatigue 값 검증 및 수정
    print(f"원본 Fatigue 범위: {df['fatigue'].min()} ~ {df['fatigue'].max()}")

    # 0 이하 값은 1로 변경 (최소 피로도)
    if (df['fatigue'] <= 0).any():
        invalid_count = (df['fatigue'] <= 0).sum()
        print(f"⚠️  0 이하 값 {invalid_count}개를 1로 변경")
        df.loc[df['fatigue'] <= 0, 'fatigue'] = 1

    # 6 이상 값은 5로 변경 (최대 피로도)
    if (df['fatigue'] > 5).any():
        invalid_count = (df['fatigue'] > 5).sum()
        print(f"⚠️  5 초과 값 {invalid_count}개를 5로 변경")
        df.loc[df['fatigue'] > 5, 'fatigue'] = 5

    print(f"수정 후 Fatigue 범위: {df['fatigue'].min()} ~ {df['fatigue'].max()}")

    # 3-Class 매핑: 1-2 → Low(0), 3 → Medium(1), 4-5 → High(2)
    print(f"\n3-Class 매핑 적용:")
    print(f"  Low (1-2)    → 0")
    print(f"  Medium (3)   → 1")
    print(f"  High (4-5)   → 2")

    # 제외할 컬럼
    exclude_columns = [
        'participant',
        'date',
        'fatigue',  # 타겟
        'mood',     # 다른 wellness 변수 (리크 방지)
        'stress',
        'sleep_quality',
        'soreness'
    ]

    # 피처 선택
    feature_columns = [col for col in df.columns if col not in exclude_columns]

    X = df[feature_columns].values

    # 3-Class 매핑 적용
    y_original = df['fatigue'].values.astype(int)
    y = np.array([config.CLASS_MAPPING[val] for val in y_original])

    groups = df['participant'].values

    print(f"✓ Features: {len(feature_columns)}")
    print(f"✓ Samples: {len(X)}")
    print(f"✓ Participants: {len(np.unique(groups))}")
    print(f"\nTarget distribution (3-Class):")
    for i in range(config.NUM_CLASSES):
        count = np.sum(y == i)
        print(f"  {config.CLASS_NAMES[i]:8s} ({i}): {count:4d} ({count/len(y)*100:.1f}%)")

    return X, y, groups, feature_columns


def create_param_distributions():
    """RandomSearch용 파라미터 분포 정의"""
    param_dist = {
        # 트리 구조
        'n_estimators': randint(100, 500),
        'max_depth': randint(3, 10),
        'min_child_weight': randint(1, 10),

        # 학습률
        'learning_rate': uniform(0.01, 0.29),  # 0.01 ~ 0.3

        # 샘플링
        'subsample': uniform(0.6, 0.4),  # 0.6 ~ 1.0
        'colsample_bytree': uniform(0.6, 0.4),

        # 정규화
        'gamma': uniform(0, 0.5),
        'reg_alpha': uniform(0, 1),
        'reg_lambda': uniform(1, 2)
    }

    return param_dist


def train_with_random_search(X, y, groups, feature_columns):
    """RandomizedSearchCV로 모델 학습"""
    print(f"\n{'#'*60}")
    print(f"# Training XGBoost with RandomizedSearchCV")
    print(f"{'#'*60}\n")

    # XGBoost 분류기
    xgb_model = xgb.XGBClassifier(
        objective='multi:softmax',
        num_class=config.NUM_CLASSES,
        random_state=config.RANDOM_STATE,
        n_jobs=4,  # CV fold별로 4개 스레드 사용 (더 공격적)
        tree_method='hist',  # 빠른 학습
        eval_metric='mlogloss'
    )

    # 파라미터 분포
    param_dist = create_param_distributions()

    # Leave-One-Group-Out CV
    logo = LeaveOneGroupOut()
    n_splits = logo.get_n_splits(X, y, groups)

    print(f"Cross-Validation Strategy: Leave-One-Participant-Out")
    print(f"Number of folds: {n_splits}")
    print(f"RandomSearch iterations: {config.RANDOM_SEARCH_ITERATIONS}\n")

    # RandomizedSearchCV
    random_search = RandomizedSearchCV(
        estimator=xgb_model,
        param_distributions=param_dist,
        n_iter=config.RANDOM_SEARCH_ITERATIONS,
        cv=logo,
        scoring=config.SCORING_METRIC,
        n_jobs=-1,  # 모든 CPU 코어 사용
        verbose=1,  # 1: 조합 완료시만 출력, 2: 각 fold 출력
        random_state=config.RANDOM_STATE,
        return_train_score=True,
        pre_dispatch='3*n_jobs'  # 더 많은 작업 미리 할당
    )

    # 학습 시작
    print(f"{'='*60}")
    print(f"Starting training...")
    print(f"{'='*60}\n")

    start_time = time.time()
    random_search.fit(X, y, groups=groups)
    elapsed_time = time.time() - start_time

    print(f"\n{'='*60}")
    print(f"✓ Training completed!")
    print(f"  Time elapsed: {elapsed_time/60:.1f} minutes")
    print(f"{'='*60}\n")

    # 최적 파라미터
    print(f"Best parameters:")
    for param, value in random_search.best_params_.items():
        print(f"  {param:20s}: {value}")

    print(f"\nBest CV score ({config.SCORING_METRIC}): {random_search.best_score_:.4f}")

    return random_search


def save_model_and_results(random_search, feature_columns):
    """모델 및 결과 저장"""
    print(f"\n{'='*60}")
    print(f"Saving model and results...")
    print(f"{'='*60}")

    # 1. 최적 모델 저장
    model_file = config.MODEL_DIR / "xgboost_best_model.pkl"
    with open(model_file, 'wb') as f:
        pickle.dump(random_search.best_estimator_, f)
    print(f"✓ Model saved to {model_file}")

    # 2. RandomSearch 객체 저장 (전체 결과 포함)
    search_file = config.MODEL_DIR / "random_search_results.pkl"
    with open(search_file, 'wb') as f:
        pickle.dump(random_search, f)
    print(f"✓ Search results saved to {search_file}")

    # 3. CV 결과 저장
    cv_results_df = pd.DataFrame(random_search.cv_results_)
    cv_results_file = config.RESULTS_DIR / "cv_results.csv"
    cv_results_df.to_csv(cv_results_file, index=False)
    print(f"✓ CV results saved to {cv_results_file}")

    # 4. 피처 중요도 저장
    feature_importance = random_search.best_estimator_.feature_importances_
    importance_df = pd.DataFrame({
        'feature': feature_columns,
        'importance': feature_importance
    }).sort_values('importance', ascending=False)

    importance_file = config.RESULTS_DIR / "feature_importance.csv"
    importance_df.to_csv(importance_file, index=False)
    print(f"✓ Feature importance saved to {importance_file}")

    # 상위 20개 피처 출력
    print(f"\nTop 20 features:")
    for _, row in importance_df.head(20).iterrows():
        print(f"  {row['feature']:30s}: {row['importance']:.4f}")

    # 5. 최적 파라미터 저장
    params_file = config.RESULTS_DIR / "best_parameters.txt"
    with open(params_file, 'w') as f:
        f.write("Best Hyperparameters\n")
        f.write("="*60 + "\n\n")
        for param, value in random_search.best_params_.items():
            f.write(f"{param:20s}: {value}\n")
        f.write(f"\nBest CV Score ({config.SCORING_METRIC}): {random_search.best_score_:.4f}\n")
    print(f"✓ Best parameters saved to {params_file}")


def evaluate_on_full_data(random_search, X, y):
    """전체 데이터로 성능 평가 (참고용)"""
    print(f"\n{'='*60}")
    print(f"Evaluation on full dataset (for reference):")
    print(f"{'='*60}\n")

    y_pred = random_search.best_estimator_.predict(X)

    print("Classification Report:")
    print(classification_report(
        y,
        y_pred,
        target_names=config.CLASS_NAMES,
        zero_division=0
    ))

    accuracy = accuracy_score(y, y_pred)
    f1_macro = f1_score(y, y_pred, average='macro')
    f1_weighted = f1_score(y, y_pred, average='weighted')

    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1-score (macro): {f1_macro:.4f}")
    print(f"F1-score (weighted): {f1_weighted:.4f}")

    # 결과 저장
    metrics_file = config.RESULTS_DIR / "full_dataset_metrics.txt"
    with open(metrics_file, 'w') as f:
        f.write("Full Dataset Evaluation (Reference)\n")
        f.write("="*60 + "\n\n")
        f.write(classification_report(
            y,
            y_pred,
            target_names=config.CLASS_NAMES,
            zero_division=0
        ))
        f.write(f"\nAccuracy: {accuracy:.4f}\n")
        f.write(f"F1-score (macro): {f1_macro:.4f}\n")
        f.write(f"F1-score (weighted): {f1_weighted:.4f}\n")
    print(f"\n✓ Metrics saved to {metrics_file}")


if __name__ == "__main__":
    # 데이터 로드
    input_file = config.OUTPUT_DIR / "features_engineered.csv"
    df = load_dataframe(input_file)
    print(f"✓ Loaded data from {input_file}")

    # 데이터 준비
    X, y, groups, feature_columns = prepare_data(df)

    # 학습
    random_search = train_with_random_search(X, y, groups, feature_columns)

    # 저장
    save_model_and_results(random_search, feature_columns)

    # 전체 데이터 평가
    evaluate_on_full_data(random_search, X, y)

    print(f"\n{'#'*60}")
    print(f"# Training pipeline completed successfully!")
    print(f"{'#'*60}\n")
