"""
앙상블 모델을 사용한 피로도 예측
- XGBoost + Random Forest + LightGBM
- Soft Voting
- RandomizedSearchCV를 통한 하이퍼파라미터 튜닝
"""

import numpy as np
import pandas as pd
import xgboost as xgb
import lightgbm as lgb
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.model_selection import (
    train_test_split,
    RandomizedSearchCV,
    StratifiedKFold,
    cross_val_score
)
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score
)
import pickle
import json
import sys
import os
from datetime import datetime
from scipy.stats import randint, uniform

# Add config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.features_config import (
    BIOMETRIC_FEATURES,
    get_weather_features_with_offset,
    TARGET_CLASSES,
    USER_TYPES
)


class EnsembleFatiguePipeline:
    def __init__(self, user_type='general', test_size=0.2, random_state=42, n_iter=20):
        """
        Initialize ensemble training pipeline

        Args:
            user_type: 'student', 'worker', or 'general'
            test_size: proportion of test set
            random_state: random seed
            n_iter: RandomizedSearchCV iterations
        """
        self.user_type = user_type
        self.test_size = test_size
        self.random_state = random_state
        self.n_iter = n_iter
        self.feature_columns = BIOMETRIC_FEATURES + get_weather_features_with_offset()

        # Individual models
        self.xgb_model = None
        self.rf_model = None
        self.lgb_model = None

        # Ensemble model
        self.ensemble_model = None

        # Best parameters
        self.best_params = {}

    def get_param_distributions(self):
        """하이퍼파라미터 탐색 공간 정의"""

        # XGBoost 파라미터
        xgb_params = {
            'max_depth': randint(3, 10),
            'learning_rate': uniform(0.01, 0.3),
            'n_estimators': randint(50, 200),
            'min_child_weight': randint(1, 7),
            'gamma': uniform(0, 0.5),
            'subsample': uniform(0.6, 0.4),
            'colsample_bytree': uniform(0.6, 0.4),
            'reg_alpha': uniform(0, 1),
            'reg_lambda': uniform(0, 1)
        }

        # Random Forest 파라미터
        rf_params = {
            'n_estimators': randint(50, 200),
            'max_depth': randint(3, 20),
            'min_samples_split': randint(2, 20),
            'min_samples_leaf': randint(1, 10),
            'max_features': ['sqrt', 'log2', None],
            'bootstrap': [True, False],
            'criterion': ['gini', 'entropy']
        }

        # LightGBM 파라미터
        lgb_params = {
            'max_depth': randint(3, 10),
            'learning_rate': uniform(0.01, 0.3),
            'n_estimators': randint(50, 200),
            'num_leaves': randint(20, 150),
            'min_child_samples': randint(5, 50),
            'subsample': uniform(0.6, 0.4),
            'colsample_bytree': uniform(0.6, 0.4),
            'reg_alpha': uniform(0, 1),
            'reg_lambda': uniform(0, 1)
        }

        return {
            'xgb': xgb_params,
            'rf': rf_params,
            'lgb': lgb_params
        }

    def load_data(self, data_path):
        """Load data from CSV file"""
        print(f"Loading data from {data_path}...")
        df = pd.read_csv(data_path)
        print(f"Loaded {len(df)} samples")
        return df

    def prepare_data(self, df):
        """Prepare features and labels"""
        X = df[self.feature_columns].values
        y = df['fatigue_label'].values

        print(f"\nFeature matrix shape: {X.shape}")
        print(f"Label distribution:\n{pd.Series(y).value_counts().sort_index()}")

        return X, y

    def tune_xgboost(self, X_train, y_train):
        """XGBoost 하이퍼파라미터 튜닝"""
        print("\n" + "="*70)
        print("Tuning XGBoost with RandomizedSearchCV")
        print("="*70)

        xgb_clf = xgb.XGBClassifier(
            objective='multi:softprob',
            num_class=3,
            random_state=self.random_state,
            eval_metric='mlogloss',
            use_label_encoder=False
        )

        param_dist = self.get_param_distributions()['xgb']

        random_search = RandomizedSearchCV(
            xgb_clf,
            param_distributions=param_dist,
            n_iter=self.n_iter,
            cv=5,
            scoring='f1_weighted',
            n_jobs=-1,
            random_state=self.random_state,
            verbose=1
        )

        random_search.fit(X_train, y_train)

        print(f"\nBest XGBoost parameters:")
        for param, value in random_search.best_params_.items():
            print(f"  {param}: {value}")
        print(f"Best CV score: {random_search.best_score_:.4f}")

        self.best_params['xgb'] = random_search.best_params_
        return random_search.best_estimator_

    def tune_random_forest(self, X_train, y_train):
        """Random Forest 하이퍼파라미터 튜닝"""
        print("\n" + "="*70)
        print("Tuning Random Forest with RandomizedSearchCV")
        print("="*70)

        rf_clf = RandomForestClassifier(
            random_state=self.random_state,
            n_jobs=-1
        )

        param_dist = self.get_param_distributions()['rf']

        random_search = RandomizedSearchCV(
            rf_clf,
            param_distributions=param_dist,
            n_iter=self.n_iter,
            cv=5,
            scoring='f1_weighted',
            n_jobs=-1,
            random_state=self.random_state,
            verbose=1
        )

        random_search.fit(X_train, y_train)

        print(f"\nBest Random Forest parameters:")
        for param, value in random_search.best_params_.items():
            print(f"  {param}: {value}")
        print(f"Best CV score: {random_search.best_score_:.4f}")

        self.best_params['rf'] = random_search.best_params_
        return random_search.best_estimator_

    def tune_lightgbm(self, X_train, y_train):
        """LightGBM 하이퍼파라미터 튜닝"""
        print("\n" + "="*70)
        print("Tuning LightGBM with RandomizedSearchCV")
        print("="*70)

        lgb_clf = lgb.LGBMClassifier(
            objective='multiclass',
            num_class=3,
            random_state=self.random_state,
            verbose=-1
        )

        param_dist = self.get_param_distributions()['lgb']

        random_search = RandomizedSearchCV(
            lgb_clf,
            param_distributions=param_dist,
            n_iter=self.n_iter,
            cv=5,
            scoring='f1_weighted',
            n_jobs=-1,
            random_state=self.random_state,
            verbose=1
        )

        random_search.fit(X_train, y_train)

        print(f"\nBest LightGBM parameters:")
        for param, value in random_search.best_params_.items():
            print(f"  {param}: {value}")
        print(f"Best CV score: {random_search.best_score_:.4f}")

        self.best_params['lgb'] = random_search.best_params_
        return random_search.best_estimator_

    def create_ensemble(self, X_train, y_train):
        """앙상블 모델 생성 (Soft Voting)"""
        print("\n" + "="*70)
        print("Creating Ensemble Model with Soft Voting")
        print("="*70)

        # 개별 모델 튜닝
        print("\n[1/3] Tuning individual models...")
        self.xgb_model = self.tune_xgboost(X_train, y_train)
        self.rf_model = self.tune_random_forest(X_train, y_train)
        self.lgb_model = self.tune_lightgbm(X_train, y_train)

        # Soft Voting Ensemble 생성
        print("\n[2/3] Creating Voting Classifier...")
        self.ensemble_model = VotingClassifier(
            estimators=[
                ('xgb', self.xgb_model),
                ('rf', self.rf_model),
                ('lgb', self.lgb_model)
            ],
            voting='soft',  # Soft voting (확률 기반)
            n_jobs=-1
        )

        # 앙상블 모델 학습
        print("\n[3/3] Training ensemble model...")
        self.ensemble_model.fit(X_train, y_train)

        print("\n✓ Ensemble model training completed!")
        return self.ensemble_model

    def evaluate(self, X_test, y_test):
        """모델 평가"""
        print("\n" + "="*70)
        print("Evaluating Models")
        print("="*70)

        results = {}

        # 개별 모델 평가
        models = {
            'XGBoost': self.xgb_model,
            'Random Forest': self.rf_model,
            'LightGBM': self.lgb_model,
            'Ensemble (Soft Voting)': self.ensemble_model
        }

        for model_name, model in models.items():
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)

            accuracy = accuracy_score(y_test, y_pred)
            f1_macro = f1_score(y_test, y_pred, average='macro')
            f1_weighted = f1_score(y_test, y_pred, average='weighted')

            results[model_name] = {
                'accuracy': accuracy,
                'f1_macro': f1_macro,
                'f1_weighted': f1_weighted,
                'predictions': y_pred.tolist(),
                'probabilities': y_pred_proba.tolist()
            }

            print(f"\n### {model_name}")
            print(f"Accuracy: {accuracy:.4f}")
            print(f"F1 (Macro): {f1_macro:.4f}")
            print(f"F1 (Weighted): {f1_weighted:.4f}")

        # 앙상블 모델 상세 평가
        print("\n" + "="*70)
        print("Detailed Ensemble Model Evaluation")
        print("="*70)

        y_pred = self.ensemble_model.predict(X_test)

        print("\nClassification Report:")
        print(classification_report(
            y_test,
            y_pred,
            target_names=TARGET_CLASSES,
            digits=4
        ))

        print("\nConfusion Matrix:")
        cm = confusion_matrix(y_test, y_pred)
        print(cm)

        # 상세 결과 저장
        results['ensemble_details'] = {
            'classification_report': classification_report(
                y_test,
                y_pred,
                target_names=TARGET_CLASSES,
                output_dict=True
            ),
            'confusion_matrix': cm.tolist()
        }

        return results

    def cross_validate_ensemble(self, X, y, cv=5):
        """앙상블 모델 교차 검증"""
        print("\n" + "="*70)
        print(f"Cross-Validating Ensemble Model ({cv}-Fold)")
        print("="*70)

        cv_scores = cross_val_score(
            self.ensemble_model,
            X,
            y,
            cv=cv,
            scoring='f1_weighted',
            n_jobs=-1
        )

        print(f"\nCV F1 Scores: {cv_scores}")
        print(f"Mean: {cv_scores.mean():.4f}")
        print(f"Std: {cv_scores.std():.4f}")

        return cv_scores.tolist()

    def save_models(self, output_dir):
        """모델 및 결과 저장"""
        os.makedirs(output_dir, exist_ok=True)

        # 앙상블 모델 저장
        ensemble_path = os.path.join(output_dir, f'{self.user_type}_ensemble_model.pkl')
        with open(ensemble_path, 'wb') as f:
            pickle.dump(self.ensemble_model, f)
        print(f"\n✓ Ensemble model saved to {ensemble_path}")

        # 개별 모델 저장
        models = {
            'xgb': self.xgb_model,
            'rf': self.rf_model,
            'lgb': self.lgb_model
        }

        for name, model in models.items():
            model_path = os.path.join(output_dir, f'{self.user_type}_{name}_model.pkl')
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            print(f"✓ {name.upper()} model saved to {model_path}")

        # 하이퍼파라미터 저장
        params_path = os.path.join(output_dir, f'{self.user_type}_ensemble_params.json')
        with open(params_path, 'w', encoding='utf-8') as f:
            json.dump(self.best_params, f, indent=2)
        print(f"✓ Best parameters saved to {params_path}")

        # 메타데이터 저장
        metadata = {
            'user_type': self.user_type,
            'feature_columns': self.feature_columns,
            'target_classes': TARGET_CLASSES,
            'models': ['XGBoost', 'Random Forest', 'LightGBM'],
            'voting': 'soft',
            'n_iter': self.n_iter,
            'trained_at': datetime.now().isoformat()
        }

        metadata_path = os.path.join(output_dir, f'{self.user_type}_ensemble_metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"✓ Metadata saved to {metadata_path}")

    def run_pipeline(self, data_path, output_dir):
        """전체 파이프라인 실행"""
        print("\n" + "="*80)
        print(f"Ensemble Fatigue Prediction Pipeline - {self.user_type.upper()}")
        print("="*80)

        # 데이터 로드
        df = self.load_data(data_path)
        X, y = self.prepare_data(df)

        # 데이터 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y
        )

        print(f"\nTrain set size: {len(X_train)}")
        print(f"Test set size: {len(X_test)}")

        # 앙상블 모델 생성
        self.create_ensemble(X_train, y_train)

        # 평가
        results = self.evaluate(X_test, y_test)

        # 교차 검증
        X_full = np.vstack([X_train, X_test])
        y_full = np.hstack([y_train, y_test])
        cv_scores = self.cross_validate_ensemble(X_full, y_full)

        # 결과 저장
        results['cv_scores'] = cv_scores
        results['user_type'] = self.user_type
        results['trained_at'] = datetime.now().isoformat()

        results_path = os.path.join(output_dir, f'{self.user_type}_ensemble_results.json')
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Results saved to {results_path}")

        # 모델 저장
        self.save_models(output_dir)

        print("\n" + "="*80)
        print("Pipeline completed successfully!")
        print("="*80)

        return results


def main():
    """메인 함수"""
    script_dir = os.path.dirname(__file__)
    data_dir = os.path.join(script_dir, '..', 'data')
    models_dir = os.path.join(script_dir, '..', 'models', 'ensemble')

    all_results = {}

    for user_type in USER_TYPES:
        print("\n\n" + "="*80)
        print(f"TRAINING ENSEMBLE MODEL FOR: {user_type.upper()}")
        print("="*80)

        data_path = os.path.join(data_dir, f'{user_type}_data.csv')

        pipeline = EnsembleFatiguePipeline(
            user_type=user_type,
            test_size=0.2,
            random_state=42,
            n_iter=20  # RandomizedSearchCV iterations
        )

        results = pipeline.run_pipeline(
            data_path=data_path,
            output_dir=models_dir
        )

        all_results[user_type] = results

    # 전체 요약 저장
    summary_path = os.path.join(models_dir, 'ensemble_training_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print("\n\n" + "="*80)
    print("ALL ENSEMBLE MODELS TRAINED SUCCESSFULLY!")
    print("="*80)
    print(f"\nSummary saved to {summary_path}")

    # 성능 비교 출력
    print("\n" + "="*80)
    print("ENSEMBLE MODEL PERFORMANCE COMPARISON")
    print("="*80)
    print(f"{'User Type':<15} {'Ensemble Acc':<15} {'XGB Acc':<12} {'RF Acc':<12} {'LGB Acc':<12}")
    print("-"*80)

    for user_type, results in all_results.items():
        ensemble_acc = results['Ensemble (Soft Voting)']['accuracy']
        xgb_acc = results['XGBoost']['accuracy']
        rf_acc = results['Random Forest']['accuracy']
        lgb_acc = results['LightGBM']['accuracy']

        print(f"{user_type:<15} {ensemble_acc:<15.4f} {xgb_acc:<12.4f} "
              f"{rf_acc:<12.4f} {lgb_acc:<12.4f}")


if __name__ == '__main__':
    main()
