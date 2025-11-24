"""
Generate dummy data for fatigue prediction models
"""

import numpy as np
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

# Add config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.features_config import (
    BIOMETRIC_FEATURES,
    get_weather_features_with_offset,
    TARGET_CLASS_MAPPING,
    USER_TYPES
)


class DummyDataGenerator:
    def __init__(self, user_type='general', n_samples=1000, random_seed=42):
        """
        Initialize dummy data generator

        Args:
            user_type: 'student', 'worker', or 'general'
            n_samples: number of samples to generate
            random_seed: random seed for reproducibility
        """
        self.user_type = user_type
        self.n_samples = n_samples
        self.random_seed = random_seed
        np.random.seed(random_seed)

    def generate_biometric_data(self):
        """Generate biometric data with user type specific patterns"""
        data = {}

        if self.user_type == 'student':
            # Students tend to have irregular sleep patterns, higher activity during daytime
            data['heart_rate_avg'] = np.random.normal(75, 10, self.n_samples)
            data['heart_rate_min'] = np.random.normal(60, 8, self.n_samples)
            data['heart_rate_max'] = np.random.normal(140, 20, self.n_samples)
            data['heart_rate_variability'] = np.random.normal(50, 15, self.n_samples)
            data['resting_heart_rate'] = np.random.normal(65, 8, self.n_samples)
            data['steps'] = np.random.normal(8000, 3000, self.n_samples)
            data['active_calories'] = np.random.normal(400, 150, self.n_samples)
            data['exercise_minutes'] = np.random.normal(30, 20, self.n_samples)
            data['stand_hours'] = np.random.normal(10, 3, self.n_samples)
            data['sleep_hours'] = np.random.normal(6.5, 1.5, self.n_samples)  # Less sleep
            data['sleep_quality'] = np.random.normal(65, 15, self.n_samples)
            data['blood_oxygen'] = np.random.normal(97, 2, self.n_samples)

        elif self.user_type == 'worker':
            # Workers have more regular patterns but higher stress
            data['heart_rate_avg'] = np.random.normal(72, 8, self.n_samples)
            data['heart_rate_min'] = np.random.normal(58, 7, self.n_samples)
            data['heart_rate_max'] = np.random.normal(130, 18, self.n_samples)
            data['heart_rate_variability'] = np.random.normal(45, 12, self.n_samples)
            data['resting_heart_rate'] = np.random.normal(62, 7, self.n_samples)
            data['steps'] = np.random.normal(6000, 2500, self.n_samples)  # Less steps
            data['active_calories'] = np.random.normal(300, 120, self.n_samples)
            data['exercise_minutes'] = np.random.normal(20, 15, self.n_samples)
            data['stand_hours'] = np.random.normal(8, 2, self.n_samples)
            data['sleep_hours'] = np.random.normal(7, 1, self.n_samples)
            data['sleep_quality'] = np.random.normal(70, 12, self.n_samples)
            data['blood_oxygen'] = np.random.normal(97, 2, self.n_samples)

        else:  # general
            # General population has average patterns
            data['heart_rate_avg'] = np.random.normal(70, 9, self.n_samples)
            data['heart_rate_min'] = np.random.normal(58, 8, self.n_samples)
            data['heart_rate_max'] = np.random.normal(135, 19, self.n_samples)
            data['heart_rate_variability'] = np.random.normal(48, 14, self.n_samples)
            data['resting_heart_rate'] = np.random.normal(63, 8, self.n_samples)
            data['steps'] = np.random.normal(7000, 2800, self.n_samples)
            data['active_calories'] = np.random.normal(350, 140, self.n_samples)
            data['exercise_minutes'] = np.random.normal(25, 18, self.n_samples)
            data['stand_hours'] = np.random.normal(9, 2.5, self.n_samples)
            data['sleep_hours'] = np.random.normal(7.5, 1.2, self.n_samples)
            data['sleep_quality'] = np.random.normal(72, 13, self.n_samples)
            data['blood_oxygen'] = np.random.normal(97, 2, self.n_samples)

        # Clip values to realistic ranges
        data['heart_rate_avg'] = np.clip(data['heart_rate_avg'], 50, 120)
        data['heart_rate_min'] = np.clip(data['heart_rate_min'], 40, 80)
        data['heart_rate_max'] = np.clip(data['heart_rate_max'], 100, 200)
        data['heart_rate_variability'] = np.clip(data['heart_rate_variability'], 20, 100)
        data['resting_heart_rate'] = np.clip(data['resting_heart_rate'], 45, 85)
        data['steps'] = np.clip(data['steps'], 0, 25000)
        data['active_calories'] = np.clip(data['active_calories'], 0, 1000)
        data['exercise_minutes'] = np.clip(data['exercise_minutes'], 0, 120)
        data['stand_hours'] = np.clip(data['stand_hours'], 0, 16)
        data['sleep_hours'] = np.clip(data['sleep_hours'], 3, 12)
        data['sleep_quality'] = np.clip(data['sleep_quality'], 0, 100)
        data['blood_oxygen'] = np.clip(data['blood_oxygen'], 90, 100)

        return pd.DataFrame(data)

    def generate_weather_data(self):
        """Generate weather data for different time offsets (0, 1, 3, 7 days ago)"""
        data = {}

        # Generate base weather patterns
        base_temp = np.random.normal(20, 10, self.n_samples)  # Temperature in Celsius
        base_humidity = np.random.normal(60, 20, self.n_samples)
        base_precip = np.random.exponential(2, self.n_samples)  # Precipitation
        base_wind = np.random.exponential(3, self.n_samples)
        base_pressure = np.random.normal(1013, 10, self.n_samples)
        base_uv = np.random.uniform(0, 11, self.n_samples)

        # Create features for each time offset
        for offset in [0, 1, 3, 7]:
            # Add some correlation with offset (weather changes gradually)
            noise_factor = 1 + (offset * 0.1)

            data[f'temperature_d{offset}'] = np.clip(
                base_temp + np.random.normal(0, 2 * noise_factor, self.n_samples),
                -10, 40
            )
            data[f'humidity_d{offset}'] = np.clip(
                base_humidity + np.random.normal(0, 5 * noise_factor, self.n_samples),
                0, 100
            )
            data[f'precipitation_d{offset}'] = np.clip(
                base_precip + np.random.exponential(1 * noise_factor, self.n_samples),
                0, 50
            )
            data[f'wind_speed_d{offset}'] = np.clip(
                base_wind + np.random.exponential(1 * noise_factor, self.n_samples),
                0, 30
            )
            data[f'atmospheric_pressure_d{offset}'] = np.clip(
                base_pressure + np.random.normal(0, 3 * noise_factor, self.n_samples),
                980, 1040
            )
            data[f'uv_index_d{offset}'] = np.clip(
                base_uv + np.random.normal(0, 1 * noise_factor, self.n_samples),
                0, 11
            )

        return pd.DataFrame(data)

    def generate_fatigue_labels(self, biometric_df, weather_df):
        """
        Generate fatigue labels based on biometric and weather data
        Uses rule-based logic to create realistic patterns
        """
        labels = []

        for i in range(self.n_samples):
            fatigue_score = 0

            # Biometric factors
            if biometric_df['sleep_hours'].iloc[i] < 6:
                fatigue_score += 2
            elif biometric_df['sleep_hours'].iloc[i] < 7:
                fatigue_score += 1

            if biometric_df['sleep_quality'].iloc[i] < 60:
                fatigue_score += 2
            elif biometric_df['sleep_quality'].iloc[i] < 70:
                fatigue_score += 1

            if biometric_df['heart_rate_variability'].iloc[i] < 40:
                fatigue_score += 1

            if biometric_df['exercise_minutes'].iloc[i] > 60:
                fatigue_score += 1  # Too much exercise can cause fatigue
            elif biometric_df['exercise_minutes'].iloc[i] < 10:
                fatigue_score += 1  # Too little exercise also affects fatigue

            # Weather factors
            if weather_df['temperature_d0'].iloc[i] > 30 or weather_df['temperature_d0'].iloc[i] < 5:
                fatigue_score += 1

            if weather_df['humidity_d0'].iloc[i] > 80:
                fatigue_score += 1

            if weather_df['atmospheric_pressure_d0'].iloc[i] < 1000:
                fatigue_score += 1  # Low pressure can affect fatigue

            # User type specific adjustments
            if self.user_type == 'student':
                if biometric_df['steps'].iloc[i] > 10000:
                    fatigue_score -= 1
            elif self.user_type == 'worker':
                if biometric_df['stand_hours'].iloc[i] > 10:
                    fatigue_score += 1

            # Add some randomness
            fatigue_score += np.random.randint(-1, 2)

            # Map score to labels
            if fatigue_score <= 1:
                labels.append(0)  # 좋음
            elif fatigue_score <= 4:
                labels.append(1)  # 보통
            else:
                labels.append(2)  # 나쁨

        return np.array(labels)

    def generate_dataset(self):
        """Generate complete dataset with all features and labels"""
        print(f"Generating {self.n_samples} samples for {self.user_type} model...")

        # Generate features
        biometric_df = self.generate_biometric_data()
        weather_df = self.generate_weather_data()

        # Generate labels
        labels = self.generate_fatigue_labels(biometric_df, weather_df)

        # Combine all features
        df = pd.concat([biometric_df, weather_df], axis=1)
        df['fatigue_label'] = labels

        # Add metadata
        df['user_type'] = self.user_type
        df['date'] = [datetime.now() - timedelta(days=i) for i in range(self.n_samples)]

        print(f"Generated dataset shape: {df.shape}")
        print(f"Label distribution:\n{pd.Series(labels).value_counts().sort_index()}")

        return df


def main():
    """Generate dummy data for all user types"""

    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(output_dir, exist_ok=True)

    for user_type in USER_TYPES:
        print(f"\n{'='*50}")
        print(f"Generating data for {user_type}")
        print('='*50)

        generator = DummyDataGenerator(
            user_type=user_type,
            n_samples=1000,
            random_seed=42
        )

        df = generator.generate_dataset()

        # Save to CSV
        output_path = os.path.join(output_dir, f'{user_type}_data.csv')
        df.to_csv(output_path, index=False)
        print(f"Saved to {output_path}")

    print("\n" + "="*50)
    print("All dummy data generated successfully!")
    print("="*50)


if __name__ == '__main__':
    main()
