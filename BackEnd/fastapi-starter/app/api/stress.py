"""
스트레스 감지 API
Apple Watch에서 심박수 데이터를 받아 실시간으로 스트레스를 계산
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
import sys
import os

# Stress 모듈 경로 추가
stress_module_path = os.path.join(os.path.dirname(__file__), '../../../../Model')
sys.path.insert(0, stress_module_path)

from Stress import RealtimeStressMonitor, StressLevel, StressDetector
from app.config.db import get_db
from app.models.tracking import StressAssessment

router = APIRouter(prefix="/stress", tags=["Stress Detection"])

# 사용자별 모니터 인스턴스 저장
user_monitors = {}


class HeartRateData(BaseModel):
    """심박수 데이터 모델"""
    user_id: int
    heart_rate: float  # BPM
    timestamp: datetime
    device_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "heart_rate": 75.0,
                "timestamp": "2025-11-13T12:30:00Z",
                "device_id": "apple-watch-series-9"
            }
        }


class StressResponse(BaseModel):
    """스트레스 평가 응답 모델"""
    user_id: int
    stress_level: str
    stress_level_kr: str
    stress_score: float
    confidence: float
    timestamp: datetime
    hrv_metrics: dict
    recommendations: List[str]


def get_or_create_monitor(user_id: int) -> RealtimeStressMonitor:
    """사용자별 스트레스 모니터 가져오기 또는 생성"""
    if user_id not in user_monitors:
        async def high_stress_callback(assessment):
            await handle_high_stress(user_id, assessment)

        monitor = RealtimeStressMonitor(
            window_size=60,
            update_interval=1,  # 1분 간격
            on_high_stress_alert=high_stress_callback
        )
        user_monitors[user_id] = monitor
    return user_monitors[user_id]


async def handle_high_stress(user_id: int, assessment):
    """고 스트레스 감지 시 처리"""
    print(f"[User {user_id}] 고 스트레스 감지: {assessment.stress_score:.0f}/100")

    # 스마트홈 자동화 트리거
    await trigger_stress_relief_scenario(user_id, assessment)

    # 알림 전송
    await send_push_notification(
        user_id,
        f"높은 스트레스가 감지되었습니다 ({assessment.stress_score:.0f}/100). 휴식을 취하세요."
    )


@router.post("/heart-rate", response_model=Optional[StressResponse])
async def receive_heart_rate(data: HeartRateData, db: Session = Depends(get_db)):
    """
    Apple Watch에서 심박수 데이터 수신 및 스트레스 계산 (1분마다 DB 저장)
    """
    try:
        monitor = get_or_create_monitor(data.user_id)
        assessment = monitor.add_heart_rate(data.heart_rate, data.timestamp)

        if assessment is None:
            return None

        # DB 저장 (1분마다)
        db_assessment = StressAssessment(
            user_id=data.user_id,
            stress_level=str(assessment.stress_level),
            stress_score=assessment.stress_score,
            confidence=assessment.confidence,
            hrv_metrics=assessment.hrv_metrics.to_dict(),
            timestamp=assessment.timestamp
        )
        db.add(db_assessment)
        db.commit()

        # 80점 이상이면 푸시 알림
        if assessment.stress_score >= 80:
            await send_push_notification(data.user_id, f"고 스트레스 감지: {assessment.stress_score:.0f}/100")

        detector = StressDetector()
        recommendations = detector.get_stress_recommendations(assessment)

        return StressResponse(
            user_id=data.user_id,
            stress_level=str(assessment.stress_level),
            stress_level_kr=assessment.stress_level.to_korean(),
            stress_score=assessment.stress_score,
            confidence=assessment.confidence,
            timestamp=assessment.timestamp,
            hrv_metrics=assessment.hrv_metrics.to_dict(),
            recommendations=recommendations['korean']
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스트레스 계산 오류: {str(e)}")


@router.get("/current/{user_id}", response_model=dict)
async def get_current_stress(user_id: int):
    """
    현재 스트레스 수준 조회

    - **user_id**: 사용자 ID
    """
    monitor = user_monitors.get(user_id)
    if monitor is None:
        raise HTTPException(status_code=404, detail="모니터링 데이터가 없습니다")

    current = monitor.get_current_stress()
    if current is None:
        raise HTTPException(status_code=404, detail="충분한 데이터가 수집되지 않았습니다")

    return {
        "stress_level": str(current.stress_level),
        "stress_level_kr": current.stress_level.to_korean(),
        "stress_score": current.stress_score,
        "confidence": current.confidence,
        "timestamp": current.timestamp.isoformat(),
        "hrv_metrics": current.hrv_metrics.to_dict()
    }


@router.get("/trend/{user_id}")
async def get_stress_trend(user_id: int, duration_minutes: int = 60, db: Session = Depends(get_db)):
    """
    DB에서 스트레스 트렌드 조회 (1분 단위 데이터)

    예: duration_minutes=60 → 최근 60분 데이터 60개 조회
    """
    cutoff = datetime.utcnow() - timedelta(minutes=duration_minutes)

    assessments = db.query(StressAssessment).filter(
        StressAssessment.user_id == user_id,
        StressAssessment.timestamp >= cutoff
    ).order_by(StressAssessment.timestamp.desc()).all()

    if not assessments:
        return {"trend": [], "summary": None}

    scores = [a.stress_score for a in assessments]
    levels = [StressLevel[a.stress_level] for a in assessments]

    return {
        "trend": [
            {
                "stress_level": a.stress_level,
                "stress_level_kr": StressLevel[a.stress_level].to_korean(),
                "stress_score": a.stress_score,
                "timestamp": a.timestamp.isoformat()
            }
            for a in assessments
        ],
        "summary": {
            "average_stress": sum(scores) / len(scores),
            "min_stress": min(scores),
            "max_stress": max(scores),
            "count": len(assessments),
            "duration_minutes": duration_minutes,
            "is_increasing": len(scores) >= 2 and scores[0] > scores[-1],
            "stress_level_distribution": {
                "very_low": sum(1 for l in levels if l == StressLevel.VERY_LOW),
                "low": sum(1 for l in levels if l == StressLevel.LOW),
                "moderate": sum(1 for l in levels if l == StressLevel.MODERATE),
                "high": sum(1 for l in levels if l == StressLevel.HIGH),
                "very_high": sum(1 for l in levels if l == StressLevel.VERY_HIGH)
            }
        }
    }


@router.delete("/reset/{user_id}")
async def reset_monitor(user_id: int):
    """
    사용자의 스트레스 모니터 초기화

    - **user_id**: 사용자 ID
    """
    if user_id in user_monitors:
        user_monitors[user_id].reset()
        return {"message": "모니터가 초기화되었습니다", "user_id": user_id}
    else:
        raise HTTPException(status_code=404, detail="모니터링 데이터가 없습니다")


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    실시간 스트레스 모니터링용 WebSocket

    클라이언트가 심박수 데이터를 전송하면 실시간으로 스트레스 평가 결과를 받습니다.

    전송 형식:
    {
        "heart_rate": 75.0,
        "timestamp": "2025-11-13T12:30:00Z"
    }

    응답 형식:
    {
        "type": "stress_update",
        "data": {
            "stress_level": "MODERATE",
            "stress_level_kr": "보통",
            "stress_score": 45.0,
            "heart_rate": 75.0,
            "timestamp": "2025-11-13T12:30:00Z"
        }
    }
    """
    await websocket.accept()
    monitor = get_or_create_monitor(user_id)

    try:
        while True:
            # 클라이언트로부터 심박수 데이터 수신
            data = await websocket.receive_json()
            hr = data.get("heart_rate")
            timestamp_str = data.get("timestamp")

            if not hr or not timestamp_str:
                await websocket.send_json({
                    "type": "error",
                    "message": "heart_rate와 timestamp가 필요합니다"
                })
                continue

            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

            # 스트레스 계산
            assessment = monitor.add_heart_rate(hr, timestamp)

            # 결과 전송
            if assessment:
                await websocket.send_json({
                    "type": "stress_update",
                    "data": {
                        "stress_level": str(assessment.stress_level),
                        "stress_level_kr": assessment.stress_level.to_korean(),
                        "stress_score": assessment.stress_score,
                        "confidence": assessment.confidence,
                        "heart_rate": hr,
                        "timestamp": assessment.timestamp.isoformat()
                    }
                })
            else:
                await websocket.send_json({
                    "type": "buffering",
                    "message": "데이터 수집 중...",
                    "heart_rate": hr
                })

    except WebSocketDisconnect:
        print(f"[User {user_id}] WebSocket 연결 종료")
    except Exception as e:
        print(f"[User {user_id}] WebSocket 오류: {e}")
        await websocket.close()


# 스마트홈 자동화 함수들
async def trigger_stress_relief_scenario(user_id: int, assessment):
    """스트레스 완화 시나리오 실행"""
    # TODO: 실제 스마트홈 API 호출로 교체
    print(f"[User {user_id}] 스트레스 완화 시나리오 실행")
    print(f"  - 조명 어둡게 (30%)")
    print(f"  - 이완 음악 재생")
    print(f"  - 온도 조절 (22°C)")

    # 예: 실제 구현
    # await home_automation_service.set_lights(user_id, brightness=30, color="warm")
    # await home_automation_service.play_music(user_id, playlist="relaxation")
    # await home_automation_service.set_temperature(user_id, target=22)


async def send_push_notification(user_id: int, message: str):
    """푸시 알림 전송"""
    # TODO: FCM 또는 APNs를 통한 푸시 알림 구현
    print(f"[User {user_id}] 알림: {message}")

    # 예: 실제 구현
    # await notification_service.send(user_id, {
    #     "title": "스트레스 알림",
    #     "body": message,
    #     "priority": "high"
    # })
