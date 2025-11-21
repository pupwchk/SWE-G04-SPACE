"""
Fatigue Prediction API
Apple Watch + WeatherKit 데이터를 받아 피로도 예측
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.services.fatigue_predictor import FatiguePredictor, FatiguePredictionResult
from app.config.db import get_db
from app.models.tracking import FatiguePrediction

router = APIRouter(prefix="/fatigue", tags=["Fatigue Prediction"])

# 전역 predictor 인스턴스 (앱 시작 시 모델 로드)
predictor = None


def get_predictor() -> FatiguePredictor:
    """Predictor 인스턴스 가져오기 (lazy loading)"""
    global predictor
    if predictor is None:
        predictor = FatiguePredictor()
    return predictor


class HealthData(BaseModel):
    """HealthKit 데이터 (Apple Watch)"""
    # Sleep
    sleep_duration: float = Field(..., description="총 수면 시간 (분)")
    sleep_time_in_bed: float = Field(..., description="침대에 있던 시간 (분)")
    sleep_deep: float = Field(..., description="깊은 수면 시간 (분)")
    sleep_light: float = Field(..., description="얕은 수면 시간 (분)")
    sleep_rem: float = Field(..., description="REM 수면 시간 (분)")
    sleep_wake: float = Field(..., description="수면 중 깬 시간 (분)")

    # Heart Rate
    hr_mean: float = Field(..., description="평균 심박수 (BPM)")
    hr_min: float = Field(..., description="최저 심박수 (BPM)")
    hr_max: float = Field(..., description="최고 심박수 (BPM)")
    hr_std: float = Field(..., description="심박수 표준편차")
    resting_hr: float = Field(..., description="안정시 심박수 (BPM)")

    # Activity
    total_steps: int = Field(..., description="총 걸음 수")
    total_distance: float = Field(..., description="총 이동 거리 (km)")
    total_calories: float = Field(..., description="총 소모 칼로리 (kcal)")

    # Exercise
    exercise_count: int = Field(0, description="운동 횟수")
    exercise_duration: float = Field(0, description="운동 시간 (분)")
    exercise_calories: float = Field(0, description="운동 칼로리 (kcal)")

    class Config:
        json_schema_extra = {
            "example": {
                "sleep_duration": 420,
                "sleep_time_in_bed": 450,
                "sleep_deep": 120,
                "sleep_light": 200,
                "sleep_rem": 100,
                "sleep_wake": 30,
                "hr_mean": 65,
                "hr_min": 50,
                "hr_max": 120,
                "hr_std": 15,
                "resting_hr": 55,
                "total_steps": 8000,
                "total_distance": 5.2,
                "total_calories": 2100,
                "exercise_count": 1,
                "exercise_duration": 30,
                "exercise_calories": 250
            }
        }


class WeatherData(BaseModel):
    """WeatherKit 데이터"""
    air_temperature: float = Field(..., description="기온 (°C)")
    relative_humidity: float = Field(..., description="상대 습도 (%)")
    air_pressure_at_sea_level: float = Field(..., description="해면 기압 (hPa)")
    precipitation_amount: float = Field(0, description="강수량 (mm)")
    cloud_area_fraction: float = Field(0, description="구름 면적 비율 (0-10)")
    duration_of_sunshine: float = Field(0, description="일조 시간 (분)")

    class Config:
        json_schema_extra = {
            "example": {
                "air_temperature": 15.5,
                "relative_humidity": 65.0,
                "air_pressure_at_sea_level": 1013.25,
                "precipitation_amount": 0,
                "cloud_area_fraction": 3.5,
                "duration_of_sunshine": 360
            }
        }


class FatiguePredictionRequest(BaseModel):
    """피로도 예측 요청"""
    user_id: int
    timestamp: datetime = Field(..., description="예측 시점 (당일)")
    health_data: HealthData
    weather_data: WeatherData
    historical_health: Optional[List[HealthData]] = Field(
        None,
        description="과거 7일 건강 데이터 (rolling average 계산용)"
    )
    historical_weather: Optional[List[WeatherData]] = Field(
        None,
        description="과거 7일 날씨 데이터"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "timestamp": "2025-11-14T09:00:00Z",
                "health_data": {
                    "sleep_duration": 420,
                    "sleep_time_in_bed": 450,
                    "sleep_deep": 120,
                    "sleep_light": 200,
                    "sleep_rem": 100,
                    "sleep_wake": 30,
                    "hr_mean": 65,
                    "hr_min": 50,
                    "hr_max": 120,
                    "hr_std": 15,
                    "resting_hr": 55,
                    "total_steps": 8000,
                    "total_distance": 5.2,
                    "total_calories": 2100,
                    "exercise_count": 1,
                    "exercise_duration": 30,
                    "exercise_calories": 250
                },
                "weather_data": {
                    "air_temperature": 15.5,
                    "relative_humidity": 65.0,
                    "air_pressure_at_sea_level": 1013.25,
                    "precipitation_amount": 0,
                    "cloud_area_fraction": 3.5,
                    "duration_of_sunshine": 360
                }
            }
        }


class FatiguePredictionResponse(BaseModel):
    """피로도 예측 응답"""
    user_id: int
    fatigue_level: str = Field(..., description="피로도 수준 (Low, Medium, High)")
    fatigue_level_kr: str = Field(..., description="피로도 수준 (한국어)")
    fatigue_class: int = Field(..., description="피로도 클래스 (0, 1, 2)")
    confidence: float = Field(..., description="예측 신뢰도 (0-1)")
    class_probabilities: Dict[str, float] = Field(..., description="각 클래스 확률")
    timestamp: datetime
    recommendations: List[str] = Field(..., description="권장사항")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "fatigue_level": "Low",
                "fatigue_level_kr": "낮음",
                "fatigue_class": 0,
                "confidence": 0.78,
                "class_probabilities": {
                    "Low": 0.78,
                    "Medium": 0.18,
                    "High": 0.04
                },
                "timestamp": "2025-11-14T09:00:00Z",
                "recommendations": [
                    "현재 피로도가 낮습니다. 활동적인 하루를 보내세요!",
                    "충분한 운동과 활동을 유지하세요",
                    "규칙적인 수면 패턴을 유지하세요"
                ]
            }
        }


@router.post("/predict", response_model=FatiguePredictionResponse)
async def predict_fatigue(
    request: FatiguePredictionRequest,
    db: Session = Depends(get_db)
):
    """
    피로도 예측

    Apple Watch (HealthKit) + WeatherKit 데이터를 받아 XGBoost 모델로 피로도를 예측합니다.

    **3-Class Classification:**
    - Low (0): 1-2점 (낮은 피로도)
    - Medium (1): 3점 (중간 피로도)
    - High (2): 4-5점 (높은 피로도)

    **Requirements:**
    - 당일 건강 데이터 (HealthKit)
    - 당일 날씨 데이터 (WeatherKit)
    - [선택] 과거 7일 데이터 (rolling average 계산용)
    """
    try:
        # Predictor 로드
        predictor = get_predictor()

        # 당일 데이터 통합
        current_data = {
            **request.health_data.model_dump(),
            **request.weather_data.model_dump(),
            "timestamp": request.timestamp
        }

        # 과거 데이터 통합 (있을 경우)
        historical_data = None
        if request.historical_health and request.historical_weather:
            if len(request.historical_health) == len(request.historical_weather):
                historical_data = [
                    {**h.model_dump(), **w.model_dump()}
                    for h, w in zip(request.historical_health, request.historical_weather)
                ]

        # 예측 수행
        result = predictor.predict(current_data, historical_data)

        # 권장사항 가져오기
        recommendations = predictor.get_recommendations(result)

        # DB 저장
        db_prediction = FatiguePrediction(
            user_id=request.user_id,
            fatigue_level=result.fatigue_level,
            fatigue_class=result.fatigue_class,
            confidence=result.confidence,
            class_probabilities=result.feature_values["class_probabilities"],
            timestamp=result.timestamp
        )
        db.add(db_prediction)
        db.commit()

        # 응답 생성
        fatigue_level_kr_map = {
            "Low": "낮음",
            "Medium": "보통",
            "High": "높음"
        }

        return FatiguePredictionResponse(
            user_id=request.user_id,
            fatigue_level=result.fatigue_level,
            fatigue_level_kr=fatigue_level_kr_map[result.fatigue_level],
            fatigue_class=result.fatigue_class,
            confidence=result.confidence,
            class_probabilities=result.feature_values["class_probabilities"],
            timestamp=result.timestamp,
            recommendations=recommendations["korean"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"피로도 예측 오류: {str(e)}")


@router.get("/history/{user_id}")
async def get_fatigue_history(
    user_id: int,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    사용자의 피로도 예측 기록 조회

    - **user_id**: 사용자 ID
    - **days**: 조회할 일수 (기본 7일)
    """
    from datetime import timedelta

    cutoff = datetime.utcnow() - timedelta(days=days)

    predictions = db.query(FatiguePrediction).filter(
        FatiguePrediction.user_id == user_id,
        FatiguePrediction.timestamp >= cutoff
    ).order_by(FatiguePrediction.timestamp.desc()).all()

    if not predictions:
        return {
            "user_id": user_id,
            "history": [],
            "summary": None
        }

    fatigue_level_kr_map = {
        "Low": "낮음",
        "Medium": "보통",
        "High": "높음"
    }

    history = [
        {
            "fatigue_level": p.fatigue_level,
            "fatigue_level_kr": fatigue_level_kr_map[p.fatigue_level],
            "fatigue_class": p.fatigue_class,
            "confidence": p.confidence,
            "timestamp": p.timestamp.isoformat()
        }
        for p in predictions
    ]

    # 요약 통계
    levels = [p.fatigue_class for p in predictions]
    summary = {
        "average_class": sum(levels) / len(levels),
        "count": len(predictions),
        "days": days,
        "distribution": {
            "Low": sum(1 for p in predictions if p.fatigue_level == "Low"),
            "Medium": sum(1 for p in predictions if p.fatigue_level == "Medium"),
            "High": sum(1 for p in predictions if p.fatigue_level == "High")
        }
    }

    return {
        "user_id": user_id,
        "history": history,
        "summary": summary
    }


@router.get("/feature-importance")
async def get_feature_importance(top_n: int = 20):
    """
    피처 중요도 조회

    XGBoost 모델의 피처 중요도를 반환합니다.

    - **top_n**: 상위 N개 피처 (기본 20개)
    """
    try:
        predictor = get_predictor()
        importance = predictor.get_feature_importance(top_n)

        return {
            "top_n": top_n,
            "feature_importance": importance
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"피처 중요도 조회 오류: {str(e)}")


@router.get("/model-info")
async def get_model_info():
    """
    모델 정보 조회

    학습된 XGBoost 모델의 메타데이터를 반환합니다.
    """
    try:
        predictor = get_predictor()

        return {
            "model_type": "XGBoost Classifier",
            "num_classes": 3,
            "class_names": ["Low", "Medium", "High"],
            "class_mapping": {
                "Low (0)": "Fatigue 1-2",
                "Medium (1)": "Fatigue 3",
                "High (2)": "Fatigue 4-5"
            },
            "cv_strategy": "Leave-One-Participant-Out (16 folds)",
            "features": {
                "total": 71,
                "healthkit": 65,
                "weather": 13,
                "derived": 10,
                "temporal": 7
            },
            "model_path": str(predictor.model_path)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"모델 정보 조회 오류: {str(e)}")
