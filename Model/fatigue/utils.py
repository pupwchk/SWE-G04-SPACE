"""
Utility functions for Fatigue Prediction
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def load_json_file(file_path: Path) -> List[Dict]:
    """JSON 파일 로드"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data if isinstance(data, list) else [data]
    except Exception as e:
        print(f"  ⚠️  Failed to load {file_path.name}: {e}")
        return []


def parse_datetime(date_str: str) -> Optional[datetime]:
    """ISO 8601 날짜 파싱"""
    try:
        # "2019-11-01T08:31:40.751Z" 형식
        return pd.to_datetime(date_str).tz_localize(None)
    except:
        return None


def extract_date(date_str: str) -> Optional[str]:
    """날짜만 추출 (YYYY-MM-DD)"""
    dt = parse_datetime(date_str)
    return dt.strftime("%Y-%m-%d") if dt else None


def calculate_rolling_features(df: pd.DataFrame,
                                columns: List[str],
                                window: int = 7,
                                suffix: str = "_7d_avg") -> pd.DataFrame:
    """이동 평균 계산"""
    df = df.sort_values('date').copy()

    for col in columns:
        if col in df.columns:
            df[f"{col}{suffix}"] = df[col].rolling(window=window, min_periods=1).mean()

    return df


def calculate_diff_features(df: pd.DataFrame,
                            columns: List[str],
                            suffix: str = "_diff_1d") -> pd.DataFrame:
    """전날 대비 변화량 계산"""
    df = df.sort_values('date').copy()

    for col in columns:
        if col in df.columns:
            df[f"{col}{suffix}"] = df[col].diff()

    return df


def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """시간 관련 피처 추가"""
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    df['day_of_week'] = df['date'].dt.dayofweek  # 0=월요일, 6=일요일
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['day_of_month'] = df['date'].dt.day
    df['week_of_year'] = df['date'].dt.isocalendar().week

    return df


def print_data_summary(df: pd.DataFrame, name: str = "Data"):
    """데이터 요약 출력"""
    print(f"\n{'='*60}")
    print(f"{name} Summary")
    print(f"{'='*60}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()[:10]}{'...' if len(df.columns) > 10 else ''}")
    print(f"Date range: {df['date'].min()} ~ {df['date'].max()}")
    print(f"Missing values:\n{df.isnull().sum()[df.isnull().sum() > 0]}")

    if 'participant' in df.columns:
        print(f"Participants: {df['participant'].nunique()}")
        print(f"Records per participant:\n{df['participant'].value_counts().describe()}")


def encode_participant(df: pd.DataFrame) -> pd.DataFrame:
    """참가자 ID를 숫자로 인코딩"""
    df = df.copy()

    # p01 -> 1, p02 -> 2, ...
    df['participant_encoded'] = df['participant'].str.extract(r'(\d+)').astype(int)

    return df


def handle_missing_values(df: pd.DataFrame, strategy: str = 'forward_fill') -> pd.DataFrame:
    """결측치 처리"""
    df = df.copy()

    if strategy == 'forward_fill':
        # participant 컬럼이 있는지 확인
        if 'participant' in df.columns:
            # 날짜 순 정렬 후 앞 값으로 채우기
            df = df.sort_values(['participant', 'date'])
            df = df.groupby('participant', group_keys=False).apply(lambda g: g.ffill().bfill())
        else:
            # participant 없으면 전체에 대해
            df = df.sort_values('date')
            df = df.ffill().bfill()

    elif strategy == 'mean':
        # 참가자별 평균으로 채우기
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if 'participant' in df.columns:
            df[numeric_cols] = df.groupby('participant')[numeric_cols].transform(
                lambda x: x.fillna(x.mean())
            )
        else:
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

    # 여전히 남은 결측치는 0으로
    df = df.fillna(0)

    return df


def split_by_participant(df: pd.DataFrame,
                         test_participants: List[str]) -> tuple:
    """참가자 기준으로 train/test 분리"""
    train_df = df[~df['participant'].isin(test_participants)].copy()
    test_df = df[df['participant'].isin(test_participants)].copy()

    return train_df, test_df


def save_dataframe(df: pd.DataFrame, file_path: Path, index: bool = False):
    """DataFrame을 CSV로 저장"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=index)
    print(f"✓ Saved to {file_path}")


def load_dataframe(file_path: Path) -> pd.DataFrame:
    """CSV에서 DataFrame 로드"""
    return pd.read_csv(file_path)
