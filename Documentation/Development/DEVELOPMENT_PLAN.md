# SPACE 프로젝트 개발 계획 (Phase 1: Sendbird 기반 구현)

> 최종 업데이트: 2025년 11월 22일

## 1. 목표

사용자의 피로도, 날씨, 생체 데이터를 기반으로 최적의 스마트홈 환경을 제안하고, 사용자와의 대화(텍스트/음성메시지)를 통해 기기를 제어하는 시스템의 핵심 기능 구현.

- **대화 시스템**: Sendbird (Chat API)
- **핵심 로직**: FastAPI (Python)
- **LLM**: OpenAI API (ChatGPT)
- **기기 제어**: LG ThinQ API

## 2. 아키텍처 및 모듈 설계

FastAPI 백엔드(`BackEnd/fastapi-starter/app`) 내에 다음과 같은 서비스 모듈을 중심으로 개발을 진행한다.

```
app/
├── services/
│   ├── fatigue_service.py       # 피로도 계산 서비스
│   ├── llm_service.py           # LLM1, LLM2 호출 및 프롬프트 관리
│   ├── thinq_service.py         # ThinQ API 인증 및 기기 제어
│   └── sendbird_service.py      # Sendbird API 메시지 발송
│
├── webhooks/
│   └── sendbird_webhook.py      # Sendbird 웹훅 수신 및 처리
│
├── api/
│   └── trigger.py               # '사용자 귀가' 등 이벤트 트리거 엔드포인트
│
└── main.py                      # FastAPI 앱 초기화 및 라우터 설정
```

---

## 3. 세부 개발 계획 (To-Do)

### **Phase 0: 환경 설정 및 서비스 모듈 기초 구현**

1.  **`.env` 파일 설정**
    -   `OPENAI_API_KEY`, `SENDBIRD_APP_ID`, `SENDBIRD_API_TOKEN`
    -   `THINQ_PAT`, `THINQ_API_KEY`, `THINQ_CLIENT_ID` 등 ThinQ 관련 모든 환경 변수 추가.

2.  **`services/fatigue_service.py` 구현**
    -   `BioWeatherConditionScorer` 클래스를 사용하여 피로도 점수를 계산하는 함수 구현.
    -   **`calculate_fatigue(health_data: dict, history_mean: dict) -> dict`**: 피로도 점수 및 관련 컨텍스트를 담은 딕셔너리 반환.

3.  **`services/thinq_service.py` 구현**
    -   **`_get_headers() -> dict`**: `.env`의 값을 바탕으로 ThinQ API 요청에 필요한 헤더 생성.
    -   **`register_client_if_needed()`**: 백엔드 시작 시 ThinQ 클라이언트 등록 로직.
    -   **`control_device(device_id: str, command_body: dict) -> bool`**: 생성된 명령어로 실제 기기 제어 요청 실행. 성공/실패 여부 반환.
    -   **`get_user_devices(user_id: str) -> list`**: 사용자의 등록된 기기 목록 (특히 `deviceId`)을 DB에서 조회.

4.  **`services/llm_service.py` 구현**
    -   **`generate_device_command(fatigue_result: dict, weather_data: dict) -> dict`**: **[LLM1]** 피로도/날씨 정보를 바탕으로 ThinQ API payload의 `body` 부분을 생성하는 프롬프트 작성 및 OpenAI API 호출. JSON 형식 검증 포함.
    -   **`generate_proactive_suggestion(command_json: dict) -> str`**: **[LLM2]** 생성된 제어 명령(`c`)을 바탕으로 사용자에게 제안할 자연어 메시지 생성. (예: "에어컨을 24도로 켤까요?")
    -   **`parse_user_response(message: str) -> dict`**: **[LLM2]** 사용자의 답변에서 의도(동의/거절/수정)를 파싱.
    -   **`generate_reactive_response(...)`**: **[LLM2]** 사용자의 직접 요청을 분석하고, 후속 조치(LLM1 호출 등)를 결정하거나 단순 답변 생성.

5.  **`services/sendbird_service.py` 구현**
    -   **`send_message(user_id: str, message: str)`**: 특정 사용자에게 Sendbird 메시지 발송.

### **Phase 1: 시나리오 1 (Proactive) 구현**

1.  **`api/trigger.py` 엔드포인트 구현**
    -   `POST /triggers/user-return` 엔드포인트 생성. (사용자 귀가 이벤트 수신)
    -   Request Body: `user_id`, `health_data`, `history_mean` 등 포함.

2.  **귀가 이벤트 처리 흐름 구현**
    -   `/triggers/user-return` 호출 시,
        1.  `fatigue_service.calculate_fatigue()` 호출 → `b` 생성.
        2.  `llm_service.generate_device_command()` 호출 → `c` 생성.
        3.  `llm_service.generate_proactive_suggestion()` 호출 → 제안 메시지 생성.
        4.  `sendbird_service.send_message()` 호출 → 사용자에게 제안 메시지 발송.

3.  **`webhooks/sendbird_webhook.py` 구현**
    -   `POST /webhooks/sendbird` 엔드포인트 생성.
    -   Sendbird 웹훅 요청 수신 및 검증.
    -   **핵심 로직**: 메시지가 어느 대화(context)에 대한 답변인지 구분하는 로직 필요. (예: 제안 메시지 발송 후 특정 시간 내의 응답은 '제안에 대한 답변'으로 간주)
    -   `llm_service.parse_user_response()` 호출 → 사용자 의도 파악.
    -   **`if 의도 == '동의'`**: `thinq_service.control_device()` 호출하여 기기 제어. 성공 후 `sendbird_service`로 결과 보고.
    -   **`if 의도 == '수정'`**: 수정 내용을 포함하여 `llm_service.generate_device_command()` 재호출 → 새로운 `c'` 생성 → 기기 제어 후 결과 보고.
    -   **`if 의도 == '거절'`**: `sendbird_service`로 "알겠습니다." 등 간단한 메시지 전송 후 종료.

### **Phase 2: 시나리오 2 (Reactive) 구현**

1.  **`webhooks/sendbird_webhook.py` 로직 확장**
    -   '제안에 대한 답변'이 아닌, 일반 사용자 요청(context가 없는 메시지)을 처리하는 로직 추가.
    -   **음성 메시지 처리**: `message_type`이 `FILE`이고 오디오 파일일 경우, 파일 URL을 STT 서비스(예: AWS Transcribe)에 보내 텍스트로 변환.
    -   변환된 텍스트 또는 원래의 텍스트 메시지를 `llm_service.generate_reactive_response()`에 전달.

2.  **`llm_service.generate_reactive_response` 로직 구체화**
    -   사용자 요청 분석 후,
        -   단순 정보성 질문이면, 바로 답변 생성.
        -   기기 제어 요청이면,
            1.  필요 시 `fatigue_service` 호출.
            2.  `llm_service.generate_device_command()` 호출하여 `c` 생성.
            3.  `thinq_service.control_device()` 호출하여 기기 제어.
            4.  최종 실행 결과를 자연어 답변으로 생성.

3.  **최종 결과 보고**
    -   `generate_reactive_response`가 생성한 최종 답변을 `sendbird_service.send_message`를 통해 사용자에게 전송.

## 4. 데이터베이스 모델 (필요시)

-   **UserDevices**: `user_id`, `device_id`, `device_type`, `nickname` 등 사용자가 등록한 기기 정보를 저장할 테이블.
-   **ConversationLog**: LLM과의 대화 내용을 기록하여 추후 서비스 개선에 활용할 로그 테이블.

---
이 계획에 따라 단계별로 개발을 진행하며, 각 단계 완료 시마다 테스트를 통해 안정성을 확보한다.
