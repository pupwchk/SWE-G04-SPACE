# 홈 위치 기반 알림 기능 요구사항 정의서

## 1. 개요

### 1.1 목적
사용자가 집/기숙사 등 주요 위치에 접근할 때 자동으로 알림을 받을 수 있는 기능을 제공하여 사용자 경험을 향상시킨다.

### 1.2 범위
- 홈 위치(집, 기숙사 등) 설정 및 저장
- 타임라인에서 위치별 태그 관리
- 홈 위치 1km 이내 접근 시 알림 발송
- 타임라인에서 홈 위치 시각적 표시

---

## 2. 기능 요구사항

### 2.1 홈 위치 저장 기능

#### FR-1: 위치 태그 설정
- **설명**: 사용자가 타임라인의 특정 위치에 "집", "기숙사" 등의 태그를 추가할 수 있어야 한다.
- **우선순위**: High
- **세부사항**:
  - 타임라인의 체크포인트에서 위치 태그 추가 가능
  - 태그 종류: 집, 기숙사, 회사, 학교 등 사용자 정의 가능
  - 하나의 위치에 여러 개의 태그 추가 가능
  - 태그는 좌표(위도, 경도)와 함께 저장

#### FR-2: 홈 위치 데이터 저장
- **설명**: 태그가 설정된 위치 정보를 Supabase에 영구 저장해야 한다.
- **우선순위**: High
- **데이터 구조**:
  ```swift
  struct TaggedLocation {
      let id: UUID
      let userId: String
      let coordinate: CLLocationCoordinate2D
      let tag: String  // "집", "기숙사" 등
      let customName: String?  // 사용자 정의 이름
      let createdAt: Date
      let updatedAt: Date
  }
  ```

#### FR-3: 홈 위치 수정/삭제
- **설명**: 저장된 홈 위치를 수정하거나 삭제할 수 있어야 한다.
- **우선순위**: Medium
- **세부사항**:
  - 태그 변경 가능
  - 위치 삭제 가능
  - 변경 이력 추적

---

### 2.2 타임라인 UI 개선

#### FR-4: 타임라인에서 태그 추가 인터페이스
- **설명**: 타임라인의 각 체크포인트에서 위치 태그를 추가할 수 있는 UI를 제공해야 한다.
- **우선순위**: High
- **세부사항**:
  - 체크포인트 상세 화면에 "위치 태그 추가" 버튼
  - 태그 선택 시트/모달 표시
  - 기본 태그: 집, 기숙사, 회사, 학교, 카페, 기타
  - 커스텀 태그 입력 가능

#### FR-5: 홈 위치 시각적 표시
- **설명**: 타임라인에서 홈 위치로 설정된 체크포인트를 시각적으로 구별할 수 있어야 한다.
- **우선순위**: High
- **세부사항**:
  - 홈 아이콘(🏠) 표시
  - 다른 체크포인트와 색상 차별화
  - 태그 이름 항상 표시
  - 지도에서 홈 위치 핀 강조 표시

#### FR-6: 홈 위치 필터링
- **설명**: 타임라인에서 홈 위치만 필터링하여 볼 수 있어야 한다.
- **우선순위**: Low
- **세부사항**:
  - "홈 위치만 보기" 토글
  - 태그별 필터링 (집, 기숙사 등)

---

### 2.3 근접 알림 기능

#### FR-7: 1km 이내 접근 감지
- **설명**: 사용자가 저장된 홈 위치로부터 1km 이내에 접근하면 감지해야 한다.
- **우선순위**: High
- **세부사항**:
  - LocationManager에서 실시간 위치와 홈 위치 간 거리 계산
  - 배터리 효율을 위한 최적화 (과도한 거리 계산 방지)
  - 백그라운드에서도 동작

#### FR-8: 알림 발송
- **설명**: 홈 위치 1km 이내 접근 시 사용자에게 알림을 발송해야 한다.
- **우선순위**: High
- **세부사항**:
  - 로컬 푸시 알림 사용
  - 알림 내용: "집 근처에 도착했습니다" 등
  - 알림 발송 후 일정 시간(예: 1시간) 동안 중복 알림 방지
  - 사용자가 알림 설정 on/off 가능

#### FR-9: 알림 커스터마이징
- **설명**: 사용자가 알림 설정을 커스터마이징할 수 있어야 한다.
- **우선순위**: Medium
- **세부사항**:
  - 알림 활성화/비활성화 토글
  - 거리 임계값 조정 (500m, 1km, 2km)
  - 특정 태그에 대해서만 알림 받기
  - 조용한 시간대 설정 (알림 받지 않을 시간)

---

## 3. 비기능 요구사항

### 3.1 성능
- **NFR-1**: 위치 거리 계산은 1초 이내에 완료되어야 한다.
- **NFR-2**: 알림 발송은 조건 만족 후 3초 이내에 이루어져야 한다.
- **NFR-3**: 백그라운드 위치 추적으로 인한 배터리 소모는 하루 10% 이하여야 한다.

### 3.2 사용성
- **NFR-4**: 위치 태그 추가는 3번의 탭 이내로 완료 가능해야 한다.
- **NFR-5**: 홈 위치 아이콘은 타임라인에서 명확하게 식별 가능해야 한다.

### 3.3 신뢰성
- **NFR-6**: GPS 오차를 고려하여 거리 계산에 ±50m 오차 범위를 적용해야 한다.
- **NFR-7**: 네트워크 연결이 없어도 로컬 캐시를 통해 홈 위치 정보에 접근 가능해야 한다.

### 3.4 보안
- **NFR-8**: 홈 위치 정보는 사용자별로 격리되어 저장되어야 한다.
- **NFR-9**: 위치 정보는 암호화되어 저장되어야 한다.

---

## 4. 데이터베이스 스키마

### 4.1 tagged_locations 테이블
```sql
CREATE TABLE tagged_locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    tag VARCHAR(50) NOT NULL,  -- '집', '기숙사', '회사' 등
    custom_name VARCHAR(100),  -- 사용자 정의 이름
    is_home BOOLEAN DEFAULT FALSE,  -- 홈 위치 여부
    notification_enabled BOOLEAN DEFAULT TRUE,  -- 알림 활성화 여부
    notification_radius INTEGER DEFAULT 1000,  -- 알림 거리 (미터)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tagged_locations_user_id ON tagged_locations(user_id);
CREATE INDEX idx_tagged_locations_is_home ON tagged_locations(is_home);
```

### 4.2 location_notifications 테이블
```sql
CREATE TABLE location_notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    tagged_location_id UUID NOT NULL REFERENCES tagged_locations(id),
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    distance_meters INTEGER,  -- 알림 발송 시점의 거리
    acknowledged BOOLEAN DEFAULT FALSE  -- 사용자가 알림 확인했는지
);

CREATE INDEX idx_location_notifications_user_id ON location_notifications(user_id);
CREATE INDEX idx_location_notifications_triggered_at ON location_notifications(triggered_at);
```

---

## 5. 구현 단계

### Phase 1: 데이터 모델 및 저장소 구현 (Week 1)
- [ ] `TaggedLocation` 모델 생성
- [ ] Supabase 테이블 생성 (tagged_locations, location_notifications)
- [ ] `TaggedLocationManager` 클래스 구현
- [ ] CRUD 기능 구현

### Phase 2: UI 구현 (Week 1-2)
- [ ] 타임라인 상세 화면에 "위치 태그 추가" 버튼 추가
- [ ] 태그 선택 시트 UI 구현
- [ ] 홈 위치 아이콘 및 시각적 표시 구현
- [ ] 설정 화면에 알림 커스터마이징 UI 추가

### Phase 3: 근접 감지 및 알림 구현 (Week 2)
- [ ] LocationManager에 홈 위치 거리 계산 로직 추가
- [ ] 1km 이내 접근 감지 구현
- [ ] 로컬 푸시 알림 설정 및 발송
- [ ] 중복 알림 방지 로직 구현

### Phase 4: 최적화 및 테스트 (Week 3)
- [ ] 배터리 소모 최적화
- [ ] 백그라운드 위치 추적 최적화
- [ ] 엣지 케이스 테스트 (GPS 오차, 네트워크 끊김 등)
- [ ] 사용자 테스트 및 피드백 반영

---

## 6. 사용자 시나리오

### 시나리오 1: 홈 위치 설정
1. 사용자가 타임라인에서 집 근처 체크포인트를 선택
2. "위치 태그 추가" 버튼 탭
3. "집" 태그 선택
4. (선택) "우리 집" 등 커스텀 이름 입력
5. 저장 버튼 탭
6. 타임라인에 🏠 아이콘과 함께 표시됨

### 시나리오 2: 귀가 시 알림 받기
1. 사용자가 외출 중
2. 집으로부터 1km 이내로 접근
3. "집 근처에 도착했습니다" 푸시 알림 수신
4. 알림 탭하면 타임라인 화면으로 이동
5. 현재 위치와 집 위치가 지도에 함께 표시됨

### 시나리오 3: 알림 설정 변경
1. 설정 화면 진입
2. "위치 알림" 섹션 선택
3. 알림 받을 태그 선택 (집만, 기숙사만 등)
4. 알림 거리 조정 (500m, 1km, 2km)
5. 조용한 시간대 설정 (23:00 - 07:00)
6. 저장

---

## 7. 추가 고려사항

### 7.1 Apple Watch 연동
- Watch에서도 홈 위치 알림 수신 가능
- Watch에서 간단한 태그 추가 가능 (프리셋만)

### 7.2 향후 확장 가능성
- 여러 홈 위치 설정 (집, 주말 별장 등)
- 시간대별 홈 위치 자동 전환 (평일: 기숙사, 주말: 집)
- 홈 위치 도착/출발 이력 통계
- 홈 위치에서의 평균 체류 시간 분석
- 경로 제안 (집까지 최적 경로)

### 7.3 프라이버시
- 홈 위치 정보는 절대 서드파티와 공유하지 않음
- 사용자가 언제든 홈 위치 데이터 삭제 가능
- 위치 데이터는 필요한 경우에만 서버에 전송

---

## 8. 성공 지표

- **채택률**: 전체 사용자의 60% 이상이 홈 위치를 설정
- **알림 정확도**: 알림의 95% 이상이 실제 1km 이내에서 발송
- **사용자 만족도**: 기능 사용자의 80% 이상이 유용하다고 평가
- **배터리 영향**: 기능 활성화로 인한 추가 배터리 소모 10% 이하
- **오탐률**: 잘못된 알림 발송률 5% 이하

---

## 9. 리스크 및 완화 방안

| 리스크 | 영향도 | 확률 | 완화 방안 |
|--------|--------|------|-----------|
| GPS 부정확으로 인한 잘못된 알림 | High | Medium | 거리 계산에 오차 범위 적용, 일정 시간 이상 머물렀을 때만 알림 |
| 배터리 과다 소모 | High | Medium | 백그라운드 위치 추적 최적화, 저전력 모드 지원 |
| 프라이버시 우려 | Medium | Low | 명확한 개인정보 처리방침, 로컬 우선 저장 |
| 네트워크 연결 불안정 | Medium | Medium | 로컬 캐싱, 오프라인 모드 지원 |

---

**작성일**: 2025-11-27
**작성자**: Development Team
**버전**: 1.0
