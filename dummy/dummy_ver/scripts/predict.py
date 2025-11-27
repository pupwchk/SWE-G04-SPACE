"""
Prediction script for fatigue prediction using trained XGBoost models
"""

import numpy as np
import pandas as pd
import xgboost as xgb
import json
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


class FatiguePredictor:
    def __init__(self, user_type='general', model_dir=None):
        """
        Initialize fatigue predictor

        Args:
            user_type: 'student', 'worker', or 'general'
            model_dir: directory containing trained models
        """
        if user_type not in USER_TYPES:
            raise ValueError(f"Invalid user_type. Must be one of {USER_TYPES}")

        self.user_type = user_type

        # Set model directory
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        self.model_dir = model_dir

        # Load model and metadata
        self.model = None
        self.metadata = None
        self.load_model()

    def load_model(self):
        """Load trained model and metadata"""
        model_path = os.path.join(self.model_dir, f'{self.user_type}_model.json')
        metadata_path = os.path.join(self.model_dir, f'{self.user_type}_metadata.json')

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        # Load XGBoost model
        self.model = xgb.Booster()
        self.model.load_model(model_path)

        # Load metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)

        print(f"Loaded {self.user_type} model trained at {self.metadata['trained_at']}")

    def prepare_features(self, features_dict):
        """
        Prepare features from dictionary

        Args:
            features_dict: Dictionary containing feature values

        Returns:
            numpy array of features in correct order
        """
        feature_columns = self.metadata['feature_columns']
        feature_values = []

        for feature in feature_columns:
            if feature not in features_dict:
                raise ValueError(f"Missing feature: {feature}")
            feature_values.append(features_dict[feature])

        return np.array([feature_values])

    def predict(self, features_dict):
        """
        Predict fatigue level

        Args:
            features_dict: Dictionary containing all required features

        Returns:
            Dictionary with prediction results
        """
        # Prepare features
        X = self.prepare_features(features_dict)

        # Create DMatrix
        dmatrix = xgb.DMatrix(X)

        # Predict probabilities
        proba = self.model.predict(dmatrix)[0]

        # Get predicted class
        predicted_class = int(np.argmax(proba))
        predicted_label = TARGET_CLASSES[predicted_class]

        # Create result dictionary
        result = {
            'user_type': self.user_type,
            'predicted_class': predicted_class,
            'predicted_label': predicted_label,
            'probabilities': {
                TARGET_CLASSES[i]: float(proba[i])
                for i in range(len(TARGET_CLASSES))
            },
            'confidence': float(proba[predicted_class])
        }

        return result

    def predict_batch(self, features_list):
        """
        Predict fatigue levels for multiple samples

        Args:
            features_list: List of feature dictionaries

        Returns:
            List of prediction results
        """
        results = []
        for features_dict in features_list:
            result = self.predict(features_dict)
            results.append(result)

        return results


def create_sample_input(user_type='general'):
    """
    Create sample input for testing

    Args:
        user_type: User type for sample generation

    Returns:
        Dictionary with sample features
    """
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
        features['sleep_hours'] = 5.5  # Low sleep - should predict higher fatigue
        features['sleep_quality'] = 55  # Low quality
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
        features['sleep_hours'] = 7.5  # Good sleep
        features['sleep_quality'] = 75  # Good quality
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
        features['sleep_hours'] = 8.0  # Good sleep
        features['sleep_quality'] = 80  # Good quality
        features['blood_oxygen'] = 97

    # Sample weather data (same for all user types)
    for offset in [0, 1, 3, 7]:
        features[f'temperature_d{offset}'] = 20 + offset * 0.5
        features[f'humidity_d{offset}'] = 60 + offset * 2
        features[f'precipitation_d{offset}'] = 0.5
        features[f'wind_speed_d{offset}'] = 3.0
        features[f'atmospheric_pressure_d{offset}'] = 1013 - offset
        features[f'uv_index_d{offset}'] = 5.0

    return features


def main():
    """Test prediction script with sample data"""
    print("="*70)
    print("Fatigue Prediction Demo")
    print("="*70)

    for user_type in USER_TYPES:
        print(f"\n{'='*70}")
        print(f"Testing {user_type.upper()} Model")
        print('='*70)

        # Create predictor
        predictor = FatiguePredictor(user_type=user_type)

        # Create sample input
        sample_features = create_sample_input(user_type)

        # Make prediction
        result = predictor.predict(sample_features)

        # Print results
        print(f"\nPrediction Results:")
        print(f"  Predicted Label: {result['predicted_label']}")
        print(f"  Confidence: {result['confidence']:.4f}")
        print(f"\n  Class Probabilities:")
        for label, prob in result['probabilities'].items():
            print(f"    {label}: {prob:.4f}")

        # Show important features
        print(f"\n  Key Input Features:")
        print(f"    Sleep Hours: {sample_features['sleep_hours']}")
        print(f"    Sleep Quality: {sample_features['sleep_quality']}")
        print(f"    Exercise Minutes: {sample_features['exercise_minutes']}")
        print(f"    Steps: {sample_features['steps']}")
        print(f"    Heart Rate Variability: {sample_features['heart_rate_variability']}")

    print("\n" + "="*70)
    print("Demo completed!")
    print("="*70)


if __name__ == '__main__':
    main()
