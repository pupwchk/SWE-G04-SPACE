"""
단일 사용자 타입에 대한 앙상블 모델 학습 (테스트용)
"""

import sys
import os

# Add current script to path
sys.path.insert(0, os.path.dirname(__file__))

from train_ensemble_model import EnsembleFatiguePipeline

def main():
    """General 모델만 학습 (테스트)"""

    script_dir = os.path.dirname(__file__)
    data_dir = os.path.join(script_dir, '..', 'data')
    models_dir = os.path.join(script_dir, '..', 'models', 'ensemble')

    user_type = 'general'  # 일반 모델만 학습

    print("="*80)
    print(f"Testing Ensemble Model Training for: {user_type.upper()}")
    print("="*80)

    data_path = os.path.join(data_dir, f'{user_type}_data.csv')

    pipeline = EnsembleFatiguePipeline(
        user_type=user_type,
        test_size=0.2,
        random_state=42,
        n_iter=10  # 테스트를 위해 iteration 줄임
    )

    results = pipeline.run_pipeline(
        data_path=data_path,
        output_dir=models_dir
    )

    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON")
    print("="*80)
    print(f"{'Model':<25} {'Accuracy':<12} {'F1 (Macro)':<12} {'F1 (Weighted)':<12}")
    print("-"*80)

    for model_name in ['XGBoost', 'Random Forest', 'LightGBM', 'Ensemble (Soft Voting)']:
        if model_name in results:
            metrics = results[model_name]
            print(f"{model_name:<25} {metrics['accuracy']:<12.4f} "
                  f"{metrics['f1_macro']:<12.4f} {metrics['f1_weighted']:<12.4f}")

if __name__ == '__main__':
    main()
