"""
HRV API 수동 테스트
"""
import sys
import os
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.db import Base
from app.models.user import User
from app.models.hrv import HRVLog
from app.services.hrv_service import hrv_service
import uuid

# SQLite 데이터베이스 생성
DATABASE_URL = "sqlite:///./test_hrv.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 테이블 생성
Base.metadata.create_all(bind=engine)

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("=" * 50)
print("HRV Service Test")
print("=" * 50)

try:
    # 1. 테스트 사용자 생성
    user_id = uuid.uuid4()  # UUID 객체로 전달
    user = User(id=user_id, email=f"test_{str(user_id)[:8]}@example.com")
    db.add(user)
    db.commit()
    print(f"✅ Test user created: {user_id}")

    # 2. HRV 데이터 동기화 테스트
    test_cases = [
        (50.0, 1, "좋음"),
        (30.0, 2, "보통"),
        (18.0, 3, "나쁨"),
        (12.0, 4, "매우 나쁨"),
    ]

    print("\n" + "=" * 50)
    print("Testing HRV sync and fatigue calculation")
    print("=" * 50)

    for hrv_value, expected_fatigue, expected_label in test_cases:
        hrv_log = hrv_service.sync_hrv_from_healthkit(
            db=db,
            user_id=user_id,
            hrv_value=hrv_value,
            measured_at=datetime.now()
        )

        assert hrv_log.fatigue_level == expected_fatigue, \
            f"Expected fatigue {expected_fatigue}, got {hrv_log.fatigue_level}"

        print(f"✅ HRV: {hrv_value}ms → Fatigue: {hrv_log.fatigue_level} ({expected_label})")

    # 3. 최신 피로도 조회 테스트
    print("\n" + "=" * 50)
    print("Testing latest fatigue level retrieval")
    print("=" * 50)

    latest_fatigue = hrv_service.get_latest_fatigue_level(db, user_id)
    print(f"✅ Latest fatigue level: {latest_fatigue}")
    assert latest_fatigue == 4, "Latest fatigue should be 4 (last inserted)"

    # 4. 평균 피로도 계산 테스트
    print("\n" + "=" * 50)
    print("Testing average fatigue calculation")
    print("=" * 50)

    avg_fatigue = hrv_service.calculate_average_fatigue(db, user_id, days=7)
    print(f"✅ Average fatigue (7 days): {avg_fatigue}")
    expected_avg = (1 + 2 + 3 + 4) / 4
    assert abs(avg_fatigue - expected_avg) < 0.01, \
        f"Expected avg {expected_avg}, got {avg_fatigue}"

    # 5. HRV 히스토리 조회 테스트
    print("\n" + "=" * 50)
    print("Testing HRV history retrieval")
    print("=" * 50)

    history = hrv_service.get_hrv_history(db, user_id, days=7)
    print(f"✅ HRV history count: {len(history)}")
    assert len(history) == 4, f"Expected 4 records, got {len(history)}"

    for log in history:
        print(f"  - HRV: {log.hrv_value}ms, Fatigue: {log.fatigue_level}, At: {log.measured_at}")

    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    print("=" * 50)

except Exception as e:
    print(f"\n❌ Test failed: {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
    # 테스트 DB 삭제
    import os
    if os.path.exists("test_hrv.db"):
        os.remove("test_hrv.db")
        print("\n🧹 Test database cleaned up")
