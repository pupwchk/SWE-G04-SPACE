"""
Step 4: Evaluation and Visualization
- Leave-One-Participant-Out 평가
- Confusion Matrix
- Feature Importance 시각화
- CV 결과 분석
"""

import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    accuracy_score
)

import config
from utils import load_dataframe


def load_trained_model():
    """학습된 모델 로드"""
    model_file = config.MODEL_DIR / "xgboost_best_model.pkl"
    with open(model_file, 'rb') as f:
        model = pickle.load(f)
    print(f"✓ Loaded model from {model_file}")
    return model


def evaluate_leave_one_out(model, X, y, groups, feature_columns):
    """Leave-One-Participant-Out 평가"""
    print(f"\n{'#'*60}")
    print(f"# Leave-One-Participant-Out Evaluation")
    print(f"{'#'*60}\n")

    logo = LeaveOneGroupOut()
    participants = np.unique(groups)

    results = []
    all_y_true = []
    all_y_pred = []

    for train_idx, test_idx in logo.split(X, y, groups):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        test_participant = groups[test_idx][0]

        # 예측
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        # 메트릭 계산
        accuracy = accuracy_score(y_test, y_pred)
        f1_macro = f1_score(y_test, y_pred, average='macro', zero_division=0)
        f1_weighted = f1_score(y_test, y_pred, average='weighted', zero_division=0)

        results.append({
            'participant': test_participant,
            'n_samples': len(y_test),
            'accuracy': accuracy,
            'f1_macro': f1_macro,
            'f1_weighted': f1_weighted
        })

        all_y_true.extend(y_test)
        all_y_pred.extend(y_pred)

        print(f"{test_participant}: Acc={accuracy:.3f}, F1(macro)={f1_macro:.3f}, F1(weighted)={f1_weighted:.3f}")

    # 결과 DataFrame
    results_df = pd.DataFrame(results)

    # 전체 평균
    print(f"\n{'='*60}")
    print(f"Overall Results:")
    print(f"{'='*60}")
    print(f"Accuracy:       {results_df['accuracy'].mean():.4f} ± {results_df['accuracy'].std():.4f}")
    print(f"F1 (macro):     {results_df['f1_macro'].mean():.4f} ± {results_df['f1_macro'].std():.4f}")
    print(f"F1 (weighted):  {results_df['f1_weighted'].mean():.4f} ± {results_df['f1_weighted'].std():.4f}")

    # 저장
    results_file = config.RESULTS_DIR / "leave_one_out_results.csv"
    results_df.to_csv(results_file, index=False)
    print(f"\n✓ Results saved to {results_file}")

    return np.array(all_y_true), np.array(all_y_pred), results_df


def plot_confusion_matrix(y_true, y_pred):
    """Confusion Matrix 시각화"""
    cm = confusion_matrix(y_true, y_pred)

    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt='d',
        cmap='Blues',
        xticklabels=config.CLASS_NAMES,
        yticklabels=config.CLASS_NAMES,
        cbar_kws={'label': 'Count'}
    )
    plt.title('Confusion Matrix - Leave-One-Participant-Out CV\n(3-Class)', fontsize=14, fontweight='bold')
    plt.xlabel('Predicted', fontsize=12)
    plt.ylabel('Actual', fontsize=12)
    plt.tight_layout()

    cm_file = config.PLOTS_DIR / "confusion_matrix.png"
    plt.savefig(cm_file, dpi=300, bbox_inches='tight')
    print(f"✓ Confusion matrix saved to {cm_file}")
    plt.close()


def plot_feature_importance():
    """Feature Importance 시각화"""
    importance_file = config.RESULTS_DIR / "feature_importance.csv"
    importance_df = pd.read_csv(importance_file)

    # 상위 20개
    top_features = importance_df.head(20)

    plt.figure(figsize=(12, 8))
    plt.barh(range(len(top_features)), top_features['importance'].values, color='steelblue')
    plt.yticks(range(len(top_features)), top_features['feature'].values)
    plt.xlabel('Importance', fontsize=12)
    plt.title('Top 20 Feature Importance', fontsize=14, fontweight='bold')
    plt.gca().invert_yaxis()
    plt.tight_layout()

    importance_plot_file = config.PLOTS_DIR / "feature_importance.png"
    plt.savefig(importance_plot_file, dpi=300, bbox_inches='tight')
    print(f"✓ Feature importance plot saved to {importance_plot_file}")
    plt.close()


def plot_cv_results():
    """RandomSearch CV 결과 시각화"""
    cv_results_file = config.RESULTS_DIR / "cv_results.csv"
    cv_results = pd.read_csv(cv_results_file)

    # CV score 분포
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 1. CV score 분포
    axes[0].hist(cv_results['mean_test_score'], bins=20, color='steelblue', edgecolor='black')
    axes[0].axvline(cv_results['mean_test_score'].max(), color='red', linestyle='--', label='Best Score')
    axes[0].set_xlabel('Mean Test Score (F1 Macro)', fontsize=12)
    axes[0].set_ylabel('Frequency', fontsize=12)
    axes[0].set_title('RandomSearch CV Score Distribution', fontsize=14, fontweight='bold')
    axes[0].legend()

    # 2. Top 10 파라미터 조합
    top_10 = cv_results.nlargest(10, 'mean_test_score')
    axes[1].barh(range(len(top_10)), top_10['mean_test_score'].values, color='darkorange')
    axes[1].set_yticks(range(len(top_10)))
    axes[1].set_yticklabels([f"#{i+1}" for i in range(len(top_10))])
    axes[1].set_xlabel('Mean Test Score (F1 Macro)', fontsize=12)
    axes[1].set_title('Top 10 Parameter Combinations', fontsize=14, fontweight='bold')
    axes[1].invert_yaxis()

    plt.tight_layout()

    cv_plot_file = config.PLOTS_DIR / "cv_results.png"
    plt.savefig(cv_plot_file, dpi=300, bbox_inches='tight')
    print(f"✓ CV results plot saved to {cv_plot_file}")
    plt.close()


def plot_participant_performance(results_df):
    """참가자별 성능 시각화"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 1. Accuracy
    axes[0].bar(results_df['participant'], results_df['accuracy'], color='steelblue')
    axes[0].axhline(results_df['accuracy'].mean(), color='red', linestyle='--', label='Mean')
    axes[0].set_xlabel('Participant', fontsize=12)
    axes[0].set_ylabel('Accuracy', fontsize=12)
    axes[0].set_title('Accuracy by Participant', fontsize=14, fontweight='bold')
    axes[0].tick_params(axis='x', rotation=45)
    axes[0].legend()

    # 2. F1 Macro
    axes[1].bar(results_df['participant'], results_df['f1_macro'], color='darkorange')
    axes[1].axhline(results_df['f1_macro'].mean(), color='red', linestyle='--', label='Mean')
    axes[1].set_xlabel('Participant', fontsize=12)
    axes[1].set_ylabel('F1 (Macro)', fontsize=12)
    axes[1].set_title('F1-Score (Macro) by Participant', fontsize=14, fontweight='bold')
    axes[1].tick_params(axis='x', rotation=45)
    axes[1].legend()

    # 3. Sample count
    axes[2].bar(results_df['participant'], results_df['n_samples'], color='green')
    axes[2].set_xlabel('Participant', fontsize=12)
    axes[2].set_ylabel('Number of Samples', fontsize=12)
    axes[2].set_title('Sample Count by Participant', fontsize=14, fontweight='bold')
    axes[2].tick_params(axis='x', rotation=45)

    plt.tight_layout()

    participant_plot_file = config.PLOTS_DIR / "participant_performance.png"
    plt.savefig(participant_plot_file, dpi=300, bbox_inches='tight')
    print(f"✓ Participant performance plot saved to {participant_plot_file}")
    plt.close()


def generate_summary_report(y_true, y_pred, results_df):
    """최종 요약 보고서 생성"""
    report_file = config.RESULTS_DIR / "evaluation_summary.txt"

    with open(report_file, 'w') as f:
        f.write("="*60 + "\n")
        f.write("FATIGUE PREDICTION MODEL - EVALUATION SUMMARY (3-Class)\n")
        f.write("="*60 + "\n\n")

        f.write("Model: XGBoost Classifier\n")
        f.write("Classes: Low (1-2), Medium (3), High (4-5)\n")
        f.write(f"CV Strategy: Leave-One-Participant-Out ({len(results_df)} folds)\n")
        f.write(f"Total Samples: {len(y_true)}\n")
        f.write(f"Features: {len(config.FITBIT_FILES)} Apple Watch compatible\n\n")

        f.write("="*60 + "\n")
        f.write("OVERALL PERFORMANCE\n")
        f.write("="*60 + "\n\n")

        f.write(f"Accuracy:       {results_df['accuracy'].mean():.4f} ± {results_df['accuracy'].std():.4f}\n")
        f.write(f"F1 (Macro):     {results_df['f1_macro'].mean():.4f} ± {results_df['f1_macro'].std():.4f}\n")
        f.write(f"F1 (Weighted):  {results_df['f1_weighted'].mean():.4f} ± {results_df['f1_weighted'].std():.4f}\n\n")

        f.write("="*60 + "\n")
        f.write("CLASSIFICATION REPORT\n")
        f.write("="*60 + "\n\n")

        f.write(classification_report(
            y_true,
            y_pred,
            target_names=config.CLASS_NAMES,
            zero_division=0
        ))

        f.write("\n" + "="*60 + "\n")
        f.write("PARTICIPANT-WISE RESULTS\n")
        f.write("="*60 + "\n\n")

        f.write(results_df.to_string(index=False))

    print(f"\n✓ Summary report saved to {report_file}")


if __name__ == "__main__":
    print(f"\n{'#'*60}")
    print(f"# Model Evaluation")
    print(f"{'#'*60}")

    # 데이터 로드
    input_file = config.OUTPUT_DIR / "features_engineered.csv"
    df = load_dataframe(input_file)

    # 데이터 준비
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

    # 3-Class 매핑
    print(f"\n3-Class 매핑 적용:")
    print(f"  Low (1-2)    → 0")
    print(f"  Medium (3)   → 1")
    print(f"  High (4-5)   → 2")

    exclude_columns = ['participant', 'date', 'fatigue', 'mood', 'stress', 'sleep_quality', 'soreness']
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

    # 모델 로드
    model = load_trained_model()

    # Leave-One-Out 평가
    y_true, y_pred, results_df = evaluate_leave_one_out(model, X, y, groups, feature_columns)

    # 시각화
    print(f"\n{'='*60}")
    print(f"Generating visualizations...")
    print(f"{'='*60}\n")

    plot_confusion_matrix(y_true, y_pred)
    plot_feature_importance()
    plot_cv_results()
    plot_participant_performance(results_df)

    # 요약 보고서
    generate_summary_report(y_true, y_pred, results_df)

    print(f"\n{'#'*60}")
    print(f"# Evaluation completed!")
    print(f"  Results directory: {config.RESULTS_DIR}")
    print(f"  Plots directory: {config.PLOTS_DIR}")
    print(f"{'#'*60}\n")
