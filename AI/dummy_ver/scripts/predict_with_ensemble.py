"""
앙상블 모델(pkl)을 사용한 예측 스크립트
"""

import pickle
import numpy as np
import pandas as pd
import sys
import os

# Add config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.features_config import (
    BIOMETRIC_FEATURES,
    get_weather_features_with_offset,
    TARGET_CLASSES,
    USER_TYPES
)


class EnsembleFatiguePredictor:
    def __init__(self, user_type='general', model_dir=None):
        """
        Initialize predictor with ensemble model

        Args:
            user_type: 'student', 'worker', or 'general'
            model_dir: directory containing ensemble models
        """
        if user_type not in USER_TYPES:
            raise ValueError(f"Invalid user_type. Must be one of {USER_TYPES}")

        self.user_type = user_type

        # Set model directory (ensemble folder)
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(__file__), '..', 'models', 'ensemble')
        self.model_dir = model_dir

        # Feature columns
        self.feature_columns = BIOMETRIC_FEATURES + get_weather_features_with_offset()

        # Load models
        self.ensemble_model = None
        self.xgb_model = None
        self.rf_model = None
        self.lgb_model = None
        self.load_models()

    def load_models(self):
        """Load all ensemble models"""
        # Load ensemble model
        ensemble_path = os.path.join(self.model_dir, f'{self.user_type}_ensemble_model.pkl')
        if os.path.exists(ensemble_path):
            print(f"Loading ensemble model from {ensemble_path}...")
            with open(ensemble_path, 'rb') as f:
                self.ensemble_model = pickle.load(f)
            print(f"✓ {self.user_type.upper()} ensemble model loaded")

        # Load individual models (optional)
        xgb_path = os.path.join(self.model_dir, f'{self.user_type}_xgb_model.pkl')
        if os.path.exists(xgb_path):
            with open(xgb_path, 'rb') as f:
                self.xgb_model = pickle.load(f)
            print(f"✓ XGBoost model loaded")

        rf_path = os.path.join(self.model_dir, f'{self.user_type}_rf_model.pkl')
        if os.path.exists(rf_path):
            with open(rf_path, 'rb') as f:
                self.rf_model = pickle.load(f)
            print(f"✓ Random Forest model loaded")

        lgb_path = os.path.join(self.model_dir, f'{self.user_type}_lgb_model.pkl')
        if os.path.exists(lgb_path):
            with open(lgb_path, 'rb') as f:
                self.lgb_model = pickle.load(f)
            print(f"✓ LightGBM model loaded")

        if self.ensemble_model is None:
            raise FileNotFoundError(f"Ensemble model not found in {self.model_dir}")

    def prepare_features(self, features_dict):
        """
        Prepare features from dictionary

        Args:
            features_dict: Dictionary containing feature values

        Returns:
            numpy array of features in correct order
        """
        feature_values = []

        for feature in self.feature_columns:
            if feature not in features_dict:
                raise ValueError(f"Missing feature: {feature}")
            feature_values.append(features_dict[feature])

        return np.array([feature_values])

    def predict(self, features_dict, use_individual=False):
        """
        Predict fatigue level

        Args:
            features_dict: Dictionary containing all required features
            use_individual: If True, also return individual model predictions

        Returns:
            Dictionary with prediction results
        """
        # Prepare features
        X = self.prepare_features(features_dict)

        # Ensemble prediction
        predicted_class = self.ensemble_model.predict(X)[0]
        probabilities = self.ensemble_model.predict_proba(X)[0]
        predicted_label = TARGET_CLASSES[predicted_class]

        # Create result dictionary
        result = {
            'user_type': self.user_type,
            'model': 'ensemble',
            'predicted_class': int(predicted_class),
            'predicted_label': predicted_label,
            'probabilities': {
                TARGET_CLASSES[i]: float(probabilities[i])
                for i in range(len(TARGET_CLASSES))
            },
            'confidence': float(probabilities[predicted_class])
        }

        # Individual model predictions (if requested and available)
        if use_individual:
            individual_preds = {}

            if self.xgb_model:
                xgb_pred = self.xgb_model.predict(X)[0]
                xgb_proba = self.xgb_model.predict_proba(X)[0]
                individual_preds['xgboost'] = {
                    'predicted_class': int(xgb_pred),
                    'predicted_label': TARGET_CLASSES[xgb_pred],
                    'confidence': float(xgb_proba[xgb_pred])
                }

            if self.rf_model:
                rf_pred = self.rf_model.predict(X)[0]
                rf_proba = self.rf_model.predict_proba(X)[0]
                individual_preds['random_forest'] = {
                    'predicted_class': int(rf_pred),
                    'predicted_label': TARGET_CLASSES[rf_pred],
                    'confidence': float(rf_proba[rf_pred])
                }

            if self.lgb_model:
                lgb_pred = self.lgb_model.predict(X)[0]
                lgb_proba = self.lgb_model.predict_proba(X)[0]
                individual_preds['lightgbm'] = {
                    'predicted_class': int(lgb_pred),
                    'predicted_label': TARGET_CLASSES[lgb_pred],
                    'confidence': float(lgb_proba[lgb_pred])
                }

            result['individual_predictions'] = individual_preds

        return result


def create_sample_input(user_type='general'):
    """Create sample input for testing"""
    features = {}

    # Sample biometric data
    if user_type == 'student':
        features['heart_rate_avg'] = 75
        features['heart_rate_min'] = 60
        features['heart_rate_max'] = 140
        features['heart_rate_variability'] = 50
        features['resting_heart_rate'] = 65
        features['steps'] = 8000
        features['active_calories'] = 400
        features['exercise_minutes'] = 30
        features['stand_hours'] = 10
        features['sleep_hours'] = 5.5
        features['sleep_quality'] = 55
        features['blood_oxygen'] = 97

    elif user_type == 'worker':
        features['heart_rate_avg'] = 72
        features['heart_rate_min'] = 58
        features['heart_rate_max'] = 130
        features['heart_rate_variability'] = 45
        features['resting_heart_rate'] = 62
        features['steps'] = 6000
        features['active_calories'] = 300
        features['exercise_minutes'] = 20
        features['stand_hours'] = 8
        features['sleep_hours'] = 7.5
        features['sleep_quality'] = 75
        features['blood_oxygen'] = 97

    else:  # general
        features['heart_rate_avg'] = 70
        features['heart_rate_min'] = 58
        features['heart_rate_max'] = 135
        features['heart_rate_variability'] = 48
        features['resting_heart_rate'] = 63
        features['steps'] = 7000
        features['active_calories'] = 350
        features['exercise_minutes'] = 25
        features['stand_hours'] = 9
        features['sleep_hours'] = 8.0
        features['sleep_quality'] = 80
        features['blood_oxygen'] = 97

    # Sample weather data
    for offset in [0, 1, 3, 7]:
        features[f'temperature_d{offset}'] = 20 + offset * 0.5
        features[f'humidity_d{offset}'] = 60 + offset * 2
        features[f'precipitation_d{offset}'] = 0.5
        features[f'wind_speed_d{offset}'] = 3.0
        features[f'atmospheric_pressure_d{offset}'] = 1013 - offset
        features[f'uv_index_d{offset}'] = 5.0

    return features


def main():
    """Test prediction with ensemble models"""
    print("="*70)
    print("Fatigue Prediction with Ensemble Models")
    print("="*70)

    for user_type in USER_TYPES:
        print(f"\n{'='*70}")
        print(f"Testing {user_type.upper()} Ensemble Model")
        print('='*70)

        # Create predictor
        try:
            predictor = EnsembleFatiguePredictor(user_type=user_type)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            continue

        # Create sample input
        sample_features = create_sample_input(user_type)

        # Make prediction with individual model breakdown
        result = predictor.predict(sample_features, use_individual=True)

        # Print ensemble results
        print(f"\n[Ensemble Prediction]")
        print(f"  Predicted Label: {result['predicted_label']}")
        print(f"  Confidence: {result['confidence']:.4f} ({result['confidence']*100:.1f}%)")
        print(f"\n  Class Probabilities:")
        for label, prob in result['probabilities'].items():
            bar = '█' * int(prob * 50)
            print(f"    {label}: {prob:.4f} {bar}")

        # Print individual model predictions
        if 'individual_predictions' in result:
            print(f"\n[Individual Model Predictions]")
            for model_name, pred in result['individual_predictions'].items():
                print(f"  {model_name.upper()}:")
                print(f"    Predicted: {pred['predicted_label']}")
                print(f"    Confidence: {pred['confidence']:.4f}")

        # Show important features
        print(f"\n  Key Input Features:")
        print(f"    Sleep Hours: {sample_features['sleep_hours']}")
        print(f"    Sleep Quality: {sample_features['sleep_quality']}")
        print(f"    Exercise Minutes: {sample_features['exercise_minutes']}")
        print(f"    Heart Rate Variability: {sample_features['heart_rate_variability']}")

    print("\n" + "="*70)
    print("Demo completed!")
    print("="*70)

    # Usage example
    print("\n" + "="*70)
    print("Quick Usage Example")
    print("="*70)
    print("""
# 1. 앙상블 모델 로드
predictor = EnsembleFatiguePredictor(user_type='student')

# 2. 피처 준비
features = {
    'heart_rate_avg': 75,
    'sleep_hours': 6.5,
    # ... (모든 필수 피처)
}

# 3. 예측 (개별 모델 결과도 함께)
result = predictor.predict(features, use_individual=True)
print(f"앙상블 예측: {result['predicted_label']}")
print(f"신뢰도: {result['confidence']:.2%}")

# 개별 모델 결과 확인
for model, pred in result['individual_predictions'].items():
    print(f"{model}: {pred['predicted_label']}")
""")


if __name__ == '__main__':
    main()
