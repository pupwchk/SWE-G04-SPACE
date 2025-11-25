# Sendbird 채팅 + 전화 백엔드 설정 가이드

이 백엔드는 **Sendbird Chat + Calls**를 사용하여 AI 페르소나와의 텍스트 채팅 및 음성 통화를 지원합니다.

## 📋 목차

1. [Sendbird 설정](#1-sendbird-설정)
2. [환경변수 설정](#2-환경변수-설정)
3. [백엔드 실행](#3-백엔드-실행)
4. [API 엔드포인트](#4-api-엔드포인트)
5. [Webhook 설정](#5-webhook-설정)
6. [테스트](#6-테스트)

---

## 1. Sendbird 설정

### 1.1 Sendbird 계정 생성

1. https://sendbird.com/ 접속
2. 회원가입 및 로그인
3. 새 Application 생성

### 1.2 Application ID 및 API Token 확인

1. Dashboard > Settings > Application
2. **Application ID** 복사
3. **API tokens** 탭에서 새 토큰 생성 또는 기존 토큰 복사

### 1.3 AI Assistant 사용자 생성

Sendbird Dashboard에서 AI 어시스턴트 사용자를 생성해야 합니다:

```bash
curl -X POST https://api-{APP_ID}.sendbird.com/v3/users \
  -H "Content-Type: application/json" \
  -H "Api-Token: {API_TOKEN}" \
  -d '{
    "user_id": "home_ai_assistant",
    "nickname": "My Home",
    "profile_url": ""
  }'
```

---

## 2. 환경변수 설정

`.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일 수정:

```env
# Sendbird 설정
SENDBIRD_APP_ID=your_actual_app_id
SENDBIRD_API_TOKEN=your_actual_api_token

# OpenAI 설정
OPENAI_API_KEY=sk-your_openai_api_key
OPENAI_MODEL=gpt-4o

# Geofence 설정 (집 위치)
HOME_LATITUDE=37.5665
HOME_LONGITUDE=126.9780
GEOFENCE_RADIUS=100.0
```

---

## 3. 백엔드 실행

### 3.1 패키지 설치

```bash
pip install -r requirements.txt
```

### 3.2 서버 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면:
- API 문서: http://localhost:8000/docs
- Webhook 엔드포인트: http://localhost:8000/webhook/sendbird/chat

---

## 4. API 엔드포인트

### 4.1 채팅 관련

#### Sendbird Webhook (자동 호출됨)
```
POST /webhook/sendbird/chat
```

#### 메시지 전송 (테스트용)
```bash
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "channel_url": "chat_user123_home_ai_assistant",
    "message": "안녕하세요"
  }'
```

### 4.2 위치 관련

#### 위치 업데이트 (iOS에서 호출)
```bash
curl -X POST http://localhost:8000/api/location/update \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "latitude": 37.5665,
    "longitude": 126.9780,
    "accuracy": 10.0
  }'
```

#### Geofence 설정
```bash
curl -X POST http://localhost:8000/api/location/geofence/config \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 37.5665,
    "longitude": 126.9780,
    "radius_meters": 100.0
  }'
```

### 4.3 음성 관련

#### STT (Speech-to-Text)
```bash
curl -X POST http://localhost:8000/api/voice/stt \
  -F "audio=@voice.wav" \
  -F "language=ko"
```

#### TTS (Text-to-Speech)
```bash
curl -X POST http://localhost:8000/api/voice/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "안녕하세요",
    "voice": "alloy"
  }' \
  --output speech.opus
```

#### 음성 대화 (STT → LLM → TTS)
```bash
curl -X POST http://localhost:8000/api/voice/conversation \
  -F "audio=@voice.wav" \
  -F "user_id=user123" \
  --output response.opus
```

---

## 5. Webhook 설정

### 5.1 Sendbird Chat Webhook

1. Dashboard > Settings > Chat > Webhooks
2. **Add webhook** 클릭
3. 설정:
   - **Webhook URL**: `https://your-domain.com/webhook/sendbird/chat`
   - **Events**: `message:send` 체크
   - **Include**: `channel`, `sender`, `payload` 체크
4. Save

### 5.2 Sendbird Calls Webhook

1. Dashboard > Calls > Settings > Webhooks
2. **Add webhook** 클릭
3. 설정:
   - **Webhook URL**: `https://your-domain.com/webhook/sendbird/calls`
   - **Events**: `call.established`, `call.ended` 체크
4. Save

### 5.3 로컬 테스트용 ngrok

로컬에서 테스트할 때는 ngrok 사용:

```bash
ngrok http 8000
```

ngrok URL을 Sendbird Webhook URL에 설정:
```
https://abc123.ngrok.io/webhook/sendbird/chat
```

---

## 6. 테스트

### 6.1 채팅 테스트

1. iOS 앱에서 로그인
2. 채팅 화면 진입
3. 메시지 전송: "안녕하세요"
4. AI 응답 확인

### 6.2 전화 테스트

1. 채팅에서 "전화해줘" 입력
2. AI가 자동으로 전화 발신
3. iOS에서 CallKit 화면 표시
4. 통화 수락

### 6.3 Geofence 테스트

1. iOS 앱에서 위치 권한 허용
2. 집 근처로 이동 (100m 이내)
3. 자동으로 채팅 메시지 수신
4. 자동으로 전화 수신

---

## 7. 시스템 아키텍처

```
┌─────────────┐
│  iOS App    │
│             │
│ - Chat UI   │
│ - Call UI   │
│ - GPS       │
└──────┬──────┘
       │
       │ HTTP/WebSocket
       │
┌──────▼──────────────────────────────────────┐
│           FastAPI Backend                   │
│                                              │
│  ┌─────────────────────────────────────┐   │
│  │  Webhook Handler                    │   │
│  │  - Sendbird Chat Webhook            │   │
│  │  - Sendbird Calls Webhook           │   │
│  └─────────────┬───────────────────────┘   │
│                │                             │
│  ┌─────────────▼───────────────────────┐   │
│  │  LLM Service                        │   │
│  │  - OpenAI GPT-4o                    │   │
│  │  - Action Parser (NONE/CALL/AUTO)   │   │
│  │  - Memory Management                │   │
│  └─────────────┬───────────────────────┘   │
│                │                             │
│  ┌─────────────▼───────────────────────┐   │
│  │  Sendbird Client                    │   │
│  │  - Chat API (send message)          │   │
│  │  - Calls API (make call)            │   │
│  └─────────────────────────────────────┘   │
│                                              │
│  ┌─────────────────────────────────────┐   │
│  │  Geofence Service                   │   │
│  │  - Haversine distance calculation   │   │
│  │  - ENTER/EXIT event detection       │   │
│  │  - Auto-call trigger                │   │
│  └─────────────────────────────────────┘   │
│                                              │
│  ┌─────────────────────────────────────┐   │
│  │  Voice Service                      │   │
│  │  - STT (Whisper)                    │   │
│  │  - TTS (OpenAI TTS)                 │   │
│  │  - Realtime pipeline                │   │
│  └─────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
       │                           │
       │                           │
       ▼                           ▼
┌─────────────┐           ┌─────────────┐
│  Sendbird   │           │   OpenAI    │
│             │           │             │
│ - Chat      │           │ - GPT-4o    │
│ - Calls     │           │ - Whisper   │
│ - Push      │           │ - TTS       │
└─────────────┘           └─────────────┘
```

---

## 8. 주요 기능

### 8.1 텍스트 채팅
- ✅ Sendbird Chat SDK 사용
- ✅ 실시간 메시지 수신 (Webhook)
- ✅ LLM 기반 자동 응답
- ✅ 대화 히스토리 관리

### 8.2 음성 통화
- ✅ Sendbird Calls API 사용
- ✅ AI → 사용자 전화 발신
- ✅ WebRTC 기반 실시간 통화
- ✅ CallKit 통합 (iOS)

### 8.3 GPS Geofence
- ✅ Haversine 거리 계산
- ✅ 집 근처 진입 감지
- ✅ 자동 전화 트리거
- ✅ 컨텍스트 기반 메시지 생성

### 8.4 음성 처리
- ✅ STT (Whisper)
- ✅ TTS (OpenAI TTS)
- ✅ 실시간 음성 대화 파이프라인
- ⏳ WebSocket 기반 스트리밍 (TODO)

---

## 9. 트러블슈팅

### 9.1 Webhook이 호출되지 않음

- Sendbird Dashboard에서 Webhook 설정 확인
- URL이 HTTPS인지 확인 (로컬은 ngrok 사용)
- 서버 로그 확인: `tail -f logs/app.log`

### 9.2 전화가 걸리지 않음

- Sendbird Calls API Token 확인
- iOS 앱에서 VoIP push 등록 확인
- 백엔드 로그에서 API 호출 에러 확인

### 9.3 Geofence가 작동하지 않음

- iOS 앱에서 위치 권한 확인
- 백엔드 `/api/location/update` 호출 확인
- Geofence 설정 확인: `GET /api/location/geofence/config`

---

## 10. 다음 단계

- [ ] DB에 대화 히스토리 저장
- [ ] 장기 메모리 시스템 구축
- [ ] 페르소나 커스터마이징
- [ ] 실시간 음성 스트리밍 (WebSocket)
- [ ] 통화 내용 요약 및 분석
- [ ] 다중 사용자 지원
- [ ] 푸시 알림 통합

---

## 📞 문의

문제가 있으면 이슈를 남겨주세요!

