"""
XGBoost training pipeline for fatigue prediction
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
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

# Add config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.features_config import (
    BIOMETRIC_FEATURES,
    get_weather_features_with_offset,
    TARGET_CLASSES,
    USER_TYPES
)


class FatiguePredictionPipeline:
    def __init__(self, user_type='general', test_size=0.2, random_state=42):
        """
        Initialize training pipeline

        Args:
            user_type: 'student', 'worker', or 'general'
            test_size: proportion of test set
            random_state: random seed
        """
        self.user_type = user_type
        self.test_size = test_size
        self.random_state = random_state
        self.model = None
        self.feature_columns = BIOMETRIC_FEATURES + get_weather_features_with_offset()

        # XGBoost parameters optimized for multi-class classification
        self.params = {
            'objective': 'multi:softprob',
            'num_class': 3,
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 3,
            'gamma': 0.1,
            'random_state': random_state,
            'eval_metric': 'mlogloss'
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

    def train(self, X_train, y_train, X_val, y_val):
        """Train XGBoost model"""
        print("\n" + "="*50)
        print("Training XGBoost Model")
        print("="*50)

        # Create DMatrix for XGBoost
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dval = xgb.DMatrix(X_val, label=y_val)

        # Train model with early stopping
        evals = [(dtrain, 'train'), (dval, 'validation')]
        self.model = xgb.train(
            self.params,
            dtrain,
            num_boost_round=self.params['n_estimators'],
            evals=evals,
            early_stopping_rounds=20,
            verbose_eval=10
        )

        print("\nTraining completed!")
        return self.model

    def evaluate(self, X_test, y_test):
        """Evaluate model performance"""
        print("\n" + "="*50)
        print("Evaluating Model")
        print("="*50)

        dtest = xgb.DMatrix(X_test)
        y_pred_proba = self.model.predict(dtest)
        y_pred = np.argmax(y_pred_proba, axis=1)

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        f1_macro = f1_score(y_test, y_pred, average='macro')
        f1_weighted = f1_score(y_test, y_pred, average='weighted')

        print(f"\nTest Accuracy: {accuracy:.4f}")
        print(f"F1 Score (Macro): {f1_macro:.4f}")
        print(f"F1 Score (Weighted): {f1_weighted:.4f}")

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

        # Return metrics
        return {
            'accuracy': accuracy,
            'f1_macro': f1_macro,
            'f1_weighted': f1_weighted,
            'confusion_matrix': cm.tolist(),
            'classification_report': classification_report(
                y_test,
                y_pred,
                target_names=TARGET_CLASSES,
                output_dict=True
            )
        }

    def cross_validate(self, X, y, cv=5):
        """Perform cross-validation"""
        print("\n" + "="*50)
        print(f"Performing {cv}-Fold Cross-Validation")
        print("="*50)

        skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=self.random_state)
        cv_scores = []

        for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
            X_train_fold, X_val_fold = X[train_idx], X[val_idx]
            y_train_fold, y_val_fold = y[train_idx], y[val_idx]

            # Train model
            dtrain = xgb.DMatrix(X_train_fold, label=y_train_fold)
            dval = xgb.DMatrix(X_val_fold, label=y_val_fold)

            model = xgb.train(
                self.params,
                dtrain,
                num_boost_round=self.params['n_estimators'],
                evals=[(dval, 'validation')],
                early_stopping_rounds=20,
                verbose_eval=False
            )

            # Evaluate
            y_pred_proba = model.predict(dval)
            y_pred = np.argmax(y_pred_proba, axis=1)
            accuracy = accuracy_score(y_val_fold, y_pred)
            cv_scores.append(accuracy)

            print(f"Fold {fold}: Accuracy = {accuracy:.4f}")

        print(f"\nMean CV Accuracy: {np.mean(cv_scores):.4f} (+/- {np.std(cv_scores):.4f})")
        return cv_scores

    def get_feature_importance(self):
        """Get feature importance from trained model"""
        importance_dict = self.model.get_score(importance_type='weight')

        # Map feature indices to names
        feature_importance = {}
        for key, value in importance_dict.items():
            feat_idx = int(key.replace('f', ''))
            if feat_idx < len(self.feature_columns):
                feature_importance[self.feature_columns[feat_idx]] = value

        # Sort by importance
        feature_importance = dict(
            sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        )

        print("\n" + "="*50)
        print("Top 10 Feature Importances")
        print("="*50)
        for i, (feature, importance) in enumerate(list(feature_importance.items())[:10], 1):
            print(f"{i}. {feature}: {importance}")

        return feature_importance

    def save_model(self, output_dir):
        """Save trained model and metadata"""
        os.makedirs(output_dir, exist_ok=True)

        # Save XGBoost model
        model_path = os.path.join(output_dir, f'{self.user_type}_model.json')
        self.model.save_model(model_path)
        print(f"\nModel saved to {model_path}")

        # Save metadata
        metadata = {
            'user_type': self.user_type,
            'feature_columns': self.feature_columns,
            'target_classes': TARGET_CLASSES,
            'params': self.params,
            'trained_at': datetime.now().isoformat()
        }

        metadata_path = os.path.join(output_dir, f'{self.user_type}_metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"Metadata saved to {metadata_path}")

        return model_path, metadata_path

    def run_pipeline(self, data_path, output_dir, perform_cv=True):
        """Run complete training pipeline"""
        print("\n" + "="*60)
        print(f"Fatigue Prediction Model Training Pipeline - {self.user_type.upper()}")
        print("="*60)

        # Load data
        df = self.load_data(data_path)

        # Prepare data
        X, y = self.prepare_data(df)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y
        )

        print(f"\nTrain set size: {len(X_train)}")
        print(f"Test set size: {len(X_test)}")

        # Split train into train and validation
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train,
            test_size=0.2,
            random_state=self.random_state,
            stratify=y_train
        )

        print(f"Validation set size: {len(X_val)}")

        # Train model
        self.train(X_train, y_train, X_val, y_val)

        # Evaluate on test set
        metrics = self.evaluate(X_test, y_test)

        # Get feature importance
        feature_importance = self.get_feature_importance()

        # Cross-validation
        if perform_cv:
            # Use original train+val set for CV
            X_train_full = np.vstack([X_train, X_val])
            y_train_full = np.hstack([y_train, y_val])
            cv_scores = self.cross_validate(X_train_full, y_train_full)
        else:
            cv_scores = None

        # Save model
        model_path, metadata_path = self.save_model(output_dir)

        # Save evaluation results
        results = {
            'user_type': self.user_type,
            'metrics': metrics,
            'feature_importance': feature_importance,
            'cv_scores': cv_scores,
            'trained_at': datetime.now().isoformat()
        }

        results_path = os.path.join(output_dir, f'{self.user_type}_results.json')
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {results_path}")

        print("\n" + "="*60)
        print("Pipeline completed successfully!")
        print("="*60)

        return results


def main():
    """Train models for all user types"""
    script_dir = os.path.dirname(__file__)
    data_dir = os.path.join(script_dir, '..', 'data')
    models_dir = os.path.join(script_dir, '..', 'models')

    all_results = {}

    for user_type in USER_TYPES:
        print("\n\n" + "="*70)
        print(f"TRAINING MODEL FOR: {user_type.upper()}")
        print("="*70)

        data_path = os.path.join(data_dir, f'{user_type}_data.csv')

        pipeline = FatiguePredictionPipeline(
            user_type=user_type,
            test_size=0.2,
            random_state=42
        )

        results = pipeline.run_pipeline(
            data_path=data_path,
            output_dir=models_dir,
            perform_cv=True
        )

        all_results[user_type] = results

    # Save summary
    summary_path = os.path.join(models_dir, 'training_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print("\n\n" + "="*70)
    print("ALL MODELS TRAINED SUCCESSFULLY!")
    print("="*70)
    print(f"\nSummary saved to {summary_path}")

    # Print comparison
    print("\n" + "="*70)
    print("MODEL PERFORMANCE COMPARISON")
    print("="*70)
    print(f"{'User Type':<15} {'Accuracy':<12} {'F1 (Macro)':<12} {'F1 (Weighted)':<12}")
    print("-"*70)
    for user_type, results in all_results.items():
        metrics = results['metrics']
        print(f"{user_type:<15} {metrics['accuracy']:<12.4f} "
              f"{metrics['f1_macro']:<12.4f} {metrics['f1_weighted']:<12.4f}")


if __name__ == '__main__':
    main()
