"""
학습된 모델들의 성능을 종합적으로 평가하는 스크립트
"""

import json
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Add config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.features_config import TARGET_CLASSES, USER_TYPES


class ModelEvaluator:
    def __init__(self, models_dir=None):
        """
        Initialize model evaluator

        Args:
            models_dir: 모델과 결과 파일이 저장된 디렉토리
        """
        if models_dir is None:
            models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        self.models_dir = models_dir
        self.results = {}
        self.load_results()

    def load_results(self):
        """모든 모델의 결과 파일 로드"""
        for user_type in USER_TYPES:
            results_path = os.path.join(self.models_dir, f'{user_type}_results.json')

            if os.path.exists(results_path):
                with open(results_path, 'r', encoding='utf-8') as f:
                    self.results[user_type] = json.load(f)
                print(f"✓ Loaded results for {user_type} model")
            else:
                print(f"✗ Results not found for {user_type} model: {results_path}")

    def print_performance_summary(self):
        """전체 성능 요약 출력"""
        print("\n" + "="*80)
        print("모델 성능 평가 종합 리포트")
        print("="*80)

        # 성능 비교 테이블
        print("\n### 1. 전체 성능 비교")
        print("-"*80)
        print(f"{'User Type':<15} {'Accuracy':<12} {'F1 (Macro)':<15} {'F1 (Weighted)':<15} {'CV Mean':<12}")
        print("-"*80)

        for user_type in USER_TYPES:
            if user_type not in self.results:
                continue

            metrics = self.results[user_type]['metrics']
            cv_scores = self.results[user_type].get('cv_scores', [])
            cv_mean = np.mean(cv_scores) if cv_scores else 0

            print(f"{user_type:<15} "
                  f"{metrics['accuracy']:<12.4f} "
                  f"{metrics['f1_macro']:<15.4f} "
                  f"{metrics['f1_weighted']:<15.4f} "
                  f"{cv_mean:<12.4f}")

        print("-"*80)

    def print_class_performance(self):
        """클래스별 성능 출력"""
        print("\n### 2. 클래스별 성능 분석")
        print("="*80)

        for user_type in USER_TYPES:
            if user_type not in self.results:
                continue

            print(f"\n[{user_type.upper()} 모델]")
            print("-"*80)

            clf_report = self.results[user_type]['metrics']['classification_report']

            print(f"{'Class':<10} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<10}")
            print("-"*80)

            for class_name in TARGET_CLASSES:
                if class_name in clf_report:
                    class_metrics = clf_report[class_name]
                    print(f"{class_name:<10} "
                          f"{class_metrics['precision']:<12.4f} "
                          f"{class_metrics['recall']:<12.4f} "
                          f"{class_metrics['f1-score']:<12.4f} "
                          f"{int(class_metrics['support']):<10}")

            print("-"*80)

    def print_confusion_matrices(self):
        """Confusion Matrix 출력"""
        print("\n### 3. Confusion Matrix 분석")
        print("="*80)

        for user_type in USER_TYPES:
            if user_type not in self.results:
                continue

            print(f"\n[{user_type.upper()} 모델 - Confusion Matrix]")
            print("-"*80)

            cm = np.array(self.results[user_type]['metrics']['confusion_matrix'])

            # 헤더 출력
            print(f"{'실제\\예측':<12}", end="")
            for class_name in TARGET_CLASSES:
                print(f"{class_name:<12}", end="")
            print()
            print("-"*60)

            # 매트릭스 출력
            for i, class_name in enumerate(TARGET_CLASSES):
                print(f"{class_name:<12}", end="")
                for j in range(len(TARGET_CLASSES)):
                    print(f"{cm[i][j]:<12}", end="")
                print()

            # 정확도 계산
            correct = np.trace(cm)
            total = np.sum(cm)
            accuracy = correct / total if total > 0 else 0

            print(f"\n정확하게 예측된 샘플: {correct}/{total} ({accuracy:.2%})")
            print("-"*80)

    def print_feature_importance(self):
        """피처 중요도 출력"""
        print("\n### 4. 주요 피처 중요도 (Top 10)")
        print("="*80)

        for user_type in USER_TYPES:
            if user_type not in self.results:
                continue

            print(f"\n[{user_type.upper()} 모델]")
            print("-"*80)

            feature_importance = self.results[user_type]['feature_importance']

            # 상위 10개 피처
            top_features = list(feature_importance.items())[:10]

            print(f"{'Rank':<6} {'Feature':<30} {'Importance':<15}")
            print("-"*60)

            for rank, (feature, importance) in enumerate(top_features, 1):
                print(f"{rank:<6} {feature:<30} {importance:<15.1f}")

            print("-"*80)

    def print_cross_validation_results(self):
        """교차 검증 결과 출력"""
        print("\n### 5. 교차 검증 결과")
        print("="*80)

        for user_type in USER_TYPES:
            if user_type not in self.results:
                continue

            cv_scores = self.results[user_type].get('cv_scores', [])

            if not cv_scores:
                continue

            print(f"\n[{user_type.upper()} 모델 - 5-Fold Cross-Validation]")
            print("-"*80)

            for fold, score in enumerate(cv_scores, 1):
                print(f"Fold {fold}: {score:.4f}")

            mean_score = np.mean(cv_scores)
            std_score = np.std(cv_scores)

            print(f"\nMean Accuracy: {mean_score:.4f}")
            print(f"Std Deviation: {std_score:.4f}")
            print(f"95% Confidence Interval: [{mean_score - 2*std_score:.4f}, {mean_score + 2*std_score:.4f}]")
            print("-"*80)

    def analyze_model_strengths_weaknesses(self):
        """모델별 강점과 약점 분석"""
        print("\n### 6. 모델별 강점 및 약점 분석")
        print("="*80)

        for user_type in USER_TYPES:
            if user_type not in self.results:
                continue

            print(f"\n[{user_type.upper()} 모델]")
            print("-"*80)

            clf_report = self.results[user_type]['metrics']['classification_report']

            # 가장 잘 예측하는 클래스
            best_class = None
            best_f1 = 0
            worst_class = None
            worst_f1 = 1

            for class_name in TARGET_CLASSES:
                if class_name in clf_report:
                    f1 = clf_report[class_name]['f1-score']
                    if f1 > best_f1:
                        best_f1 = f1
                        best_class = class_name
                    if f1 < worst_f1:
                        worst_f1 = f1
                        worst_class = class_name

            print(f"✓ 강점: '{best_class}' 클래스 예측 우수 (F1: {best_f1:.4f})")
            print(f"✗ 약점: '{worst_class}' 클래스 예측 개선 필요 (F1: {worst_f1:.4f})")

            # 정밀도 vs 재현율 분석
            metrics = self.results[user_type]['metrics']
            weighted_precision = clf_report.get('weighted avg', {}).get('precision', 0)
            weighted_recall = clf_report.get('weighted avg', {}).get('recall', 0)

            if weighted_precision > weighted_recall:
                print(f"• 특성: 정밀도 중심 (Precision: {weighted_precision:.4f} > Recall: {weighted_recall:.4f})")
                print(f"  → False Positive를 잘 제어함 (잘못된 긍정 예측이 적음)")
            else:
                print(f"• 특성: 재현율 중심 (Recall: {weighted_recall:.4f} > Precision: {weighted_precision:.4f})")
                print(f"  → False Negative를 잘 제어함 (실제 케이스를 잘 찾아냄)")

            print("-"*80)

    def generate_improvement_recommendations(self):
        """개선 권장사항 생성"""
        print("\n### 7. 개선 권장사항")
        print("="*80)

        for user_type in USER_TYPES:
            if user_type not in self.results:
                continue

            print(f"\n[{user_type.upper()} 모델]")
            print("-"*80)

            metrics = self.results[user_type]['metrics']
            accuracy = metrics['accuracy']
            f1_macro = metrics['f1_macro']

            recommendations = []

            # 정확도 기반 권장사항
            if accuracy < 0.70:
                recommendations.append("• 전체 정확도가 70% 미만: 더 많은 학습 데이터 수집 권장")
                recommendations.append("• 피처 엔지니어링 고려 (파생 변수 생성)")

            # F1 스코어 기반 권장사항
            if f1_macro < 0.60:
                recommendations.append("• F1 Macro 점수 개선 필요: 클래스 불균형 해결 (SMOTE, 가중치 조정)")

            # 클래스별 성능 기반 권장사항
            clf_report = metrics['classification_report']
            for class_name in TARGET_CLASSES:
                if class_name in clf_report:
                    class_f1 = clf_report[class_name]['f1-score']
                    if class_f1 < 0.50:
                        recommendations.append(f"• '{class_name}' 클래스 성능 저조: 해당 클래스 데이터 증강 필요")

            # CV 표준편차 기반 권장사항
            cv_scores = self.results[user_type].get('cv_scores', [])
            if cv_scores and np.std(cv_scores) > 0.05:
                recommendations.append(f"• 교차검증 표준편차 높음 ({np.std(cv_scores):.4f}): 모델 안정성 개선 필요")
                recommendations.append("  - 정규화 강화 (L1/L2 regularization)")
                recommendations.append("  - 더 많은 학습 데이터")

            if not recommendations:
                print("✓ 모델 성능이 우수합니다. 현재 설정 유지를 권장합니다.")
            else:
                for rec in recommendations:
                    print(rec)

            print("-"*80)

    def export_summary_to_file(self, output_path=None):
        """평가 결과를 파일로 저장"""
        if output_path is None:
            output_path = os.path.join(self.models_dir, 'evaluation_summary.json')

        summary = {
            'evaluation_date': pd.Timestamp.now().isoformat(),
            'models_evaluated': list(self.results.keys()),
            'summary': {}
        }

        for user_type in USER_TYPES:
            if user_type not in self.results:
                continue

            metrics = self.results[user_type]['metrics']
            cv_scores = self.results[user_type].get('cv_scores', [])

            summary['summary'][user_type] = {
                'accuracy': metrics['accuracy'],
                'f1_macro': metrics['f1_macro'],
                'f1_weighted': metrics['f1_weighted'],
                'cv_mean': float(np.mean(cv_scores)) if cv_scores else None,
                'cv_std': float(np.std(cv_scores)) if cv_scores else None
            }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\n평가 요약이 저장되었습니다: {output_path}")

    def generate_full_report(self):
        """전체 리포트 생성"""
        self.print_performance_summary()
        self.print_class_performance()
        self.print_confusion_matrices()
        self.print_feature_importance()
        self.print_cross_validation_results()
        self.analyze_model_strengths_weaknesses()
        self.generate_improvement_recommendations()
        self.export_summary_to_file()

        print("\n" + "="*80)
        print("평가 완료!")
        print("="*80)


def main():
    """메인 함수"""
    print("모델 성능 평가 시작...\n")

    evaluator = ModelEvaluator()

    if not evaluator.results:
        print("Error: 평가할 모델 결과를 찾을 수 없습니다.")
        print("먼저 train_model.py를 실행하여 모델을 학습하세요.")
        return

    evaluator.generate_full_report()


if __name__ == '__main__':
    main()
