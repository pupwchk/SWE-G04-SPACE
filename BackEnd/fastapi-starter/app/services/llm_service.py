"""
LLM 서비스 - OpenAI API를 사용한 AI 응답 생성
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# OpenAI 클라이언트 초기화
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


class LLMAction:
    """LLM 액션 타입"""
    NONE = "NONE"  # 일반 텍스트 응답


class LLMService:
    """LLM 서비스"""
    
    def __init__(self):
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    def _build_system_prompt(self, persona: Optional[Dict] = None) -> str:
        """
        시스템 프롬프트 생성

        Args:
            persona: 페르소나 정보 (말투, 성격 등)
        """
        base_prompt = """당신은 사용자의 스마트홈 AI 어시스턴트입니다.

**역할:**
- 사용자와 자연스럽게 대화
- 집안일 도움 (가전제품 제어, 일정 관리 등)
- 사용자의 상태 파악 (피로도, 스트레스 등)
- 채팅을 통해 친근하게 소통

**응답 형식:**
반드시 JSON 형식으로 응답하세요:

{
  "action": "NONE",
  "response": "응답 메시지"
}

**중요:**
- 항상 JSON만 반환하세요
- 모든 대화는 채팅을 통해 이루어집니다
- 자연스럽고 친근한 대화체를 사용하세요
"""

        if persona:
            base_prompt += f"\n**말투/성격:**\n{persona.get('description', '')}\n"

        return base_prompt
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        persona: Optional[Dict] = None,
        context: Optional[Dict] = None,
        appliance_states: Optional[List[Dict]] = None,
        dialogue_state: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        LLM 응답 생성

        Args:
            user_message: 사용자 메시지
            conversation_history: 대화 히스토리
            persona: 페르소나 정보
            context: 추가 컨텍스트 (위치, 시간, 상태 등)
            appliance_states: 현재 가전 상태 리스트
            dialogue_state: DST 상태 (intent, slots)

        Returns:
            {
                "action": "NONE",
                "response": "응답 메시지",
                ...
            }
        """
        try:
            # 메시지 구성
            messages = [
                {"role": "system", "content": self._build_system_prompt(persona)}
            ]

            # 대화 히스토리 추가
            if conversation_history:
                messages.extend(conversation_history[-10:])  # 최근 10개만

            # DST 상태 추가 (현재 대화 맥락)
            if dialogue_state and (dialogue_state.get("intent") or dialogue_state.get("slots")):
                dst_str = f"\n\n**대화 맥락 (DST):**\n"
                if dialogue_state.get("intent"):
                    dst_str += f"- 현재 의도: {dialogue_state['intent']}\n"
                if dialogue_state.get("slots"):
                    dst_str += f"- 대화 중인 주제: {json.dumps(dialogue_state['slots'], ensure_ascii=False)}\n"
                messages.append({"role": "system", "content": dst_str})

            # 가전 상태 추가
            if appliance_states:
                appliance_str = "\n\n**현재 가전 상태:**\n"
                for app in appliance_states:
                    status = "켜짐" if app.get("is_on") else "꺼짐"
                    appliance_str += f"- {app['appliance_type']}: {status}"
                    if app.get("is_on") and app.get("current_settings"):
                        appliance_str += f" (설정: {json.dumps(app['current_settings'], ensure_ascii=False)})"
                    appliance_str += "\n"
                messages.append({"role": "system", "content": appliance_str})

            # 컨텍스트 추가
            if context:
                context_str = f"\n\n**현재 상황:**\n{json.dumps(context, ensure_ascii=False, indent=2)}"
                messages.append({"role": "system", "content": context_str})

            # 사용자 메시지 추가
            messages.append({"role": "user", "content": user_message})
            
            # OpenAI API 호출
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # 응답 파싱
            content = response.choices[0].message.content
            result = json.loads(content)
            
            logger.info(f"✅ LLM response: action={result.get('action')}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM response: {e}")
            # Fallback
            return {
                "action": "NONE",
                "response": "죄송해요, 잘 이해하지 못했어요. 다시 말씀해주시겠어요?"
            }
        except Exception as e:
            logger.error(f"❌ LLM error: {str(e)}")
            return {
                "action": "NONE",
                "response": "일시적인 오류가 발생했어요. 잠시 후 다시 시도해주세요."
            }
    
    async def parse_user_intent(self, user_message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        사용자 의도 파싱 (시나리오 2용)

        "덥다" → {"type": "temperature", "condition": "hot"}
        "건조하다" → {"type": "humidity", "condition": "dry"}
        "공기 나쁘다" → {"type": "air_quality", "condition": "bad"}

        Args:
            user_message: 사용자 메시지
            context: 현재 날씨/상태 정보

        Returns:
            {
                "intent_type": "environment_complaint" | "general_chat" | "appliance_request",
                "issues": [
                    {"type": "temperature", "condition": "hot"},
                    {"type": "humidity", "condition": "dry"}
                ],
                "needs_control": true/false
            }
        """
        try:
            prompt = f"""사용자의 메시지를 분석하여 의도를 파악하세요.

사용자 메시지: "{user_message}"

다음 JSON 형식으로 응답하세요:
{{
  "intent_type": "environment_complaint" | "general_chat" | "appliance_request",
  "issues": [
    {{"type": "temperature|humidity|air_quality", "condition": "hot|cold|dry|humid|bad"}}
  ],
  "needs_control": true/false,
  "summary": "간단한 요약"
}}

**분류 기준:**
- environment_complaint: "덥다", "춥다", "건조하다", "습하다", "공기 나쁘다", "답답하다" 등 환경 불편 표현
  → 이 경우 **반드시 needs_control: true**
- appliance_request: "에어컨 켜줘", "불 켜줘" 등 직접적인 가전 제어 요청
  → 이 경우도 **반드시 needs_control: true**
- general_chat: 일반 대화 ("안녕", "고마워", "날씨 어때?" 등)
  → 이 경우만 needs_control: false

**condition 값:**
- temperature: "hot" (덥다/더워) / "cold" (춥다/추워)
- humidity: "dry" (건조하다) / "humid" (습하다)
- air_quality: "bad" (공기 나쁘다/답답하다)

**중요:** 사용자가 환경에 대한 불편함을 표현하면 무조건 needs_control: true입니다!
"""

            if context:
                prompt += f"\n\n**현재 환경:**\n{json.dumps(context, ensure_ascii=False, indent=2)}"

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 사용자 의도 파싱 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            logger.info(f"✅ Intent parsed: {result.get('intent_type')}, needs_control={result.get('needs_control')}")
            return result

        except Exception as e:
            logger.error(f"❌ Intent parsing error: {str(e)}")
            return {
                "intent_type": "general_chat",
                "issues": [],
                "needs_control": False,
                "summary": "파싱 실패"
            }

    async def generate_user_request_suggestion(
        self,
        user_message: str,
        appliance_states: List[Dict[str, Any]],
        weather: Dict[str, Any],
        fatigue_level: int,
        persona: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        사용자 요청 기반 가전 제어 제안 (조건 테이블 없이 LLM 판단)

        사용자가 "춥다", "덥다" 등을 말했을 때, 현재 가전 상태를 보고 제어 제안

        Args:
            user_message: 사용자 메시지
            appliance_states: 현재 가전 상태 리스트
            weather: 날씨 데이터
            fatigue_level: 피로도 레벨
            persona: 페르소나 정보
            conversation_history: 대화 히스토리

        Returns:
            {
                "response": "제안 메시지",
                "appliances": [
                    {
                        "appliance_type": "에어컨",
                        "action": "off",
                        "settings": {},
                        "reason": "사용자가 춥다고 했으므로"
                    },
                    ...
                ]
            }
        """
        try:
            # 현재 가전 상태 요약
            appliance_status_str = ""
            registered_appliances = []

            if appliance_states:
                appliance_status_str = "\n**사용자가 등록한 가전 목록 및 현재 상태:**\n"
                for app in appliance_states:
                    status = "켜짐" if app.get("is_on") else "꺼짐"
                    appliance_type = app['appliance_type']
                    registered_appliances.append(appliance_type)
                    appliance_status_str += f"- {appliance_type}: {status}"
                    if app.get("is_on") and app.get("current_settings"):
                        appliance_status_str += f" (설정: {json.dumps(app['current_settings'], ensure_ascii=False)})"
                    appliance_status_str += "\n"
            else:
                appliance_status_str = "\n**사용자가 등록한 가전이 없습니다.**\n"

            prompt = f"""사용자가 "{user_message}"라고 말했습니다.

**현재 상황:**
- 온도: {weather.get('temperature')}°C
- 습도: {weather.get('humidity')}%
- 미세먼지: {weather.get('pm10')} ㎍/㎥
- 피로도 레벨: {fatigue_level} (1:좋음, 2:보통, 3:나쁨, 4:매우나쁨)

{appliance_status_str}

**중요 규칙:**
1. **오직 위에 나열된 등록된 가전만** 제어 제안할 수 있습니다
2. 등록되지 않은 가전은 절대 추천하지 마세요
3. 등록된 가전이 없으면 appliances를 빈 배열로 반환하세요

사용자의 요청을 바탕으로 **등록된 가전 중에서만** 적절한 제어를 제안하세요.

예시:
- "춥다" + 에어컨이 등록되어 있음 → 에어컨 냉방이 켜져있으면 끄기 제안, 에어컨 난방 모드로 켜기 제안
- "덥다" + 에어컨이 등록되어 있음 → 에어컨 난방이 켜져있으면 끄기 제안, 에어컨 냉방 모드로 켜기 제안
- "건조하다" + 가습기가 등록되어 있음 → 가습기 켜기 제안
- "건조하다" + 가습기가 등록되어 있지 않음 → appliances: [] (빈 배열)
- "공기 나쁘다" + 공기청정기가 등록되어 있음 → 공기청정기 켜기 제안

다음 JSON 형식으로 응답하세요:
{{
  "response": "사용자에게 보낼 자연스러운 제안 메시지",
  "appliances": [
    {{
      "appliance_type": "등록된 가전의 정확한 이름 (위 목록에서만 선택)",
      "action": "on 또는 off",
      "settings": {{}},
      "reason": "제어 이유"
    }}
  ]
}}

**중요:**
- action이 "on"일 때만 settings를 포함하세요
- action이 "off"일 때는 settings를 빈 객체 {{}}로 하세요
- power_state는 settings에 포함하지 마세요 (is_on으로 별도 관리)

**가전별 settings 형식 (action: "on"일 때):**

에어컨:
{{"mode": "냉방", "target_temp_c": 23, "fan_speed": 3}}
- mode: "냉방", "제습", "송풍", "자동", "난방" 중 하나
- target_temp_c: 18~28 (정수)
- fan_speed: 1~5 (정수)

조명:
{{"brightness_pct": 80, "color_temperature_k": 3000}}
- scene: "집중", "휴식", "수면" (선택, scene 사용 시 다른 설정 생략 가능)
- brightness_pct: 0~100 (정수)
- color_temperature_k: 2700~6500, 100 단위 (선택)
- color_hex: "#RRGGBB" 형식 (선택)

공기청정기:
{{"mode": "자동", "fan_speed": 3}}
- mode: "자동", "수동", "저소음" 중 하나
- fan_speed: 1~5 (정수)
- target_pm2_5: 목표 미세먼지 수치 (선택)
- target_pm10: 목표 미세먼지 수치 (선택)
- ionizer_on: true/false (선택)

제습기:
{{"mode": "일반", "target_humidity_pct": 45, "fan_speed": 2}}
- mode: "일반", "연속", "세탁물" 중 하나
- target_humidity_pct: 35~60 (정수)
- fan_speed: 1~4 (정수)

가습기:
{{"mode": "자동", "target_humidity_pct": 50, "mist_level": 2}}
- mode: "자동", "수면", "쾌적" 중 하나
- target_humidity_pct: 40~65 (정수)
- mist_level: 1~4 (정수)
- warm_mist: true/false (선택)

TV:
{{"input_source": "OTT", "volume": 30, "brightness": 70}}
- input_source: "HDMI 1", "OTT", "게임", "음악" 중 하나
- volume: 0~100 (정수)
- brightness: 30~100 (정수)
- channel: 채널 번호 (선택)
- contrast: 대비 값 (선택)
- color: 색상 값 (선택)

**다시 한번 강조:**
- **반드시 등록된 가전만** appliances에 포함시키세요
- 등록되지 않은 가전을 추천하면 안 됩니다
- appliance_type은 위 목록의 가전 이름과 정확히 일치해야 합니다
- 등록된 가전이 없거나 적절한 가전이 없으면 appliances를 빈 배열로 하고 response에서 등록된 가전이 없다고 안내하세요
"""

            # 시스템 프롬프트 생성 (페르소나 적용)
            system_prompt = self._build_system_prompt(persona)

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            logger.info(f"✅ User request suggestion generated: {len(result.get('appliances', []))} appliances")
            return result

        except Exception as e:
            logger.error(f"❌ User request suggestion error: {str(e)}")
            return {
                "response": "죄송해요, 현재 제어 가능한 가전을 찾지 못했어요.",
                "appliances": []
            }

    async def generate_proactive_appliance_message(
        self,
        appliances: List[Dict[str, Any]],
        weather: Dict[str, Any],
        fatigue_level: int,
        persona: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        집 도착 시 가전 제어 제안 메시지 생성 (Proactive - 시나리오 1용)

        Args:
            appliances: 제어할 가전 목록
            weather: 날씨 데이터
            fatigue_level: 피로도 레벨 (1-4)
            persona: 페르소나 정보 (nickname)
            conversation_history: 대화 히스토리 (컨텍스트 유지)

        Returns:
            자연스러운 제안 메시지
        """
        try:
            appliance_info = []
            for app in appliances:
                info_parts = [f"- {app['appliance_type']}"]
                if app.get('settings'):
                    # 설정값을 자연스럽게 표현
                    settings = app['settings']
                    if 'target_temp_c' in settings:
                        info_parts.append(f"{settings['target_temp_c']}°C")
                    if 'mode' in settings:
                        info_parts.append(f"{settings['mode']} 모드")
                    if 'target_humidity_pct' in settings:
                        info_parts.append(f"습도 {settings['target_humidity_pct']}%")
                    if 'fan_speed' in settings:
                        info_parts.append(f"풍속 {settings['fan_speed']}")
                    if 'brightness_pct' in settings:
                        info_parts.append(f"밝기 {settings['brightness_pct']}%")

                appliance_info.append(" ".join(info_parts))

            # 대화 히스토리 요약
            history_context = ""
            if conversation_history and len(conversation_history) > 0:
                history_context = "\n**이전 대화 내용:**\n"
                history_context += "위 대화 히스토리를 참고하여, 이전 대화와 자연스럽게 연결되는 메시지를 작성하세요.\n"

            prompt = f"""사용자가 집에 거의 도착했습니다.
{history_context}
**현재 상황:**
- 온도: {weather.get('temperature')}°C
- 습도: {weather.get('humidity')}%
- 피로도 레벨: {fatigue_level} (1:좋음, 2:보통, 3:나쁨, 4:매우나쁨)

**AI가 분석하여 추천하는 가전 제어:**
{chr(10).join(appliance_info)}

사용자에게 친근하고 자연스럽게 **채팅으로** 가전 제어를 제안하는 메시지를 작성하세요.
**중요: 이전 대화가 있다면, 그 맥락을 고려하여 자연스럽게 이어지는 대화를 작성하세요.**

**반드시 지켜야 할 규칙:**
1. 현재 상황(온도, 습도, 피로도)을 **간단히** 한 문장으로 언급
2. 각 가전의 구체적인 설정값을 자연스럽게 포함
3. "작동시킬까요?", "켜드릴까요?" 같은 승인 요청으로 마무리
4. 형식적인 나열(예: "- 온도: X°C") 대신 자연스러운 대화체 사용
5. **절대로** "전화 드릴게요", "통화" 같은 표현 사용 금지 (채팅 메시지입니다!)
6. 200자 이내로 간결하게

**좋은 예시:**
- "집에 거의 도착하셨네요! 날씨가 춥고 피로해 보이시니 에어컨을 25도 난방 모드로 미리 켜드릴까요?"
- "곧 도착하시겠어요! 지금 온도가 낮고 건조해서 에어컨을 23도로, 가습기를 습도 50%로 켜드릴까요?"

**나쁜 예시 (절대 하지 마세요):**
- "집에 거의 도착하셨네요!\n\n현재 상황:\n- 피로도 레벨: 1\n- 온도: -1.2°C\n..." (형식적 나열)
- "추천 가전:\n- 에어컨 (target_temp_c: 25, fan_speed: 3)..." (기술적 표현)
- "전화 드릴게요", "통화 걸게요" (전화 언급 금지!)

반드시 일반 텍스트로만 응답하세요 (JSON 아님).
"""

            # 시스템 프롬프트
            system_prompt = "당신은 사용자의 스마트홈 AI 어시스턴트입니다. 친근하고 자연스럽게 대화하세요."
            if persona:
                system_prompt += f"\n당신의 이름은 {persona.get('nickname')}입니다."

            # 메시지 구성 (대화 히스토리 포함)
            messages = [{"role": "system", "content": system_prompt}]

            # 대화 히스토리 추가 (최근 5개만)
            if conversation_history:
                messages.extend(conversation_history[-5:])

            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,
                max_tokens=150
            )

            message = response.choices[0].message.content.strip()
            logger.info(f"✅ Proactive appliance message generated: {message[:50]}...")
            return message

        except Exception as e:
            logger.error(f"❌ Proactive appliance message error: {str(e)}")
            # Fallback
            appliance_names = [a["appliance_type"] for a in appliances]
            return f"집에 거의 도착하셨네요! 현재 날씨와 피로도를 고려해서 {', '.join(appliance_names)}을(를) 켜드릴까요?"

    async def generate_proactive_no_appliance_message(
        self,
        weather: Dict[str, Any],
        fatigue_level: int,
        persona: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        집 도착 시 가전 추천이 없을 때 메시지 생성 (Proactive - 시나리오 1용)

        Args:
            weather: 날씨 데이터
            fatigue_level: 피로도 레벨 (1-4)
            persona: 페르소나 정보 (nickname)
            conversation_history: 대화 히스토리 (컨텍스트 유지)

        Returns:
            자연스러운 인사 메시지
        """
        try:
            # 대화 히스토리 요약
            history_context = ""
            if conversation_history and len(conversation_history) > 0:
                history_context = "\n**이전 대화 내용:**\n"
                history_context += "위 대화 히스토리를 참고하여, 이전 대화와 자연스럽게 연결되는 메시지를 작성하세요.\n"

            prompt = f"""사용자가 집에 거의 도착했습니다.
{history_context}
**현재 상황:**
- 온도: {weather.get('temperature')}°C
- 습도: {weather.get('humidity')}%
- 피로도 레벨: {fatigue_level} (1:좋음, 2:보통, 3:나쁨, 4:매우나쁨)

AI 분석 결과, 현재 날씨와 피로도 상태가 적정 범위라 따로 켤 가전은 없습니다.

사용자에게 친근하게 집 도착을 환영하는 메시지를 작성하세요.
**중요: 이전 대화가 있다면, 그 맥락을 고려하여 자연스럽게 이어지는 대화를 작성하세요.**

**반드시 지켜야 할 규칙:**
1. 현재 상태가 괜찮다는 것을 자연스럽게 전달
2. 필요하면 언제든 말하라는 안내
3. 100자 이내로 간결하게
4. 형식적인 나열 대신 자연스러운 대화체

**좋은 예시:**
- "집에 거의 도착하셨네요! 현재 날씨와 컨디션이 괜찮아 보여요. 필요한 게 있으면 언제든 말씀해주세요!"
- "곧 도착하시겠어요! 지금 상태가 좋아 보이네요. 편히 쉬세요~"

반드시 일반 텍스트로만 응답하세요 (JSON 아님).
"""

            # 시스템 프롬프트
            system_prompt = "당신은 사용자의 스마트홈 AI 어시스턴트입니다. 친근하고 자연스럽게 대화하세요."
            if persona:
                system_prompt += f"\n당신의 이름은 {persona.get('nickname')}입니다."

            # 메시지 구성 (대화 히스토리 포함)
            messages = [{"role": "system", "content": system_prompt}]

            # 대화 히스토리 추가 (최근 5개만)
            if conversation_history:
                messages.extend(conversation_history[-5:])

            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,
                max_tokens=100
            )

            message = response.choices[0].message.content.strip()
            logger.info(f"✅ Proactive no-appliance message generated: {message[:50]}...")
            return message

        except Exception as e:
            logger.error(f"❌ Proactive no-appliance message error: {str(e)}")
            return "집에 거의 도착하셨네요! 현재 날씨와 피로도 상태가 괜찮아 보여요. 편히 쉬세요!"

    async def generate_appliance_suggestion(
        self,
        appliances: List[Dict[str, Any]],
        weather: Dict[str, Any],
        fatigue_level: int,
        user_message: str,
        persona: Optional[Dict] = None,
        appliance_states: Optional[List[Dict]] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        가전 제어 제안 메시지 생성 (시나리오 2용)

        Args:
            appliances: 제어할 가전 목록
            weather: 날씨 데이터
            fatigue_level: 피로도 레벨
            user_message: 사용자 원본 메시지
            persona: 페르소나 정보 (nickname, description)
            appliance_states: 현재 가전 상태 리스트
            conversation_history: 대화 히스토리

        Returns:
            제안 메시지 (예: "현재 온도가 28도로 높고, 피로도가 3이에요. 에어컨을 23도로 켜고, 공기청정기도 켤까요?")
        """
        try:
            appliance_info = []
            has_preference_settings = False

            for app in appliances:
                settings_source = app.get('settings_source', 'default')

                # 선호 세팅 사용 여부 표시
                if settings_source == "preference":
                    has_preference_settings = True
                    source_label = " [학습된 선호 세팅]"
                elif settings_source == "user_input":
                    source_label = " [사용자 지정값]"
                else:
                    source_label = ""

                info = f"{app['appliance_type']}: {app['settings']}{source_label}"
                if app.get('reason'):
                    info += f" ({app['reason']})"
                appliance_info.append(info)

            prompt = f"""사용자가 "{user_message}"라고 말했습니다.

**현재 상황:**
- 온도: {weather.get('temperature')}°C
- 습도: {weather.get('humidity')}%
- 미세먼지: {weather.get('pm10')} ㎍/㎥
- 피로도 레벨: {fatigue_level} (1:좋음, 2:보통, 3:나쁨, 4:매우나쁨)

**추천 가전 제어 (등록된 가전만):**
{chr(10).join(appliance_info)}
"""

            # 현재 가전 상태 추가
            if appliance_states:
                prompt += "\n**사용자가 등록한 가전의 현재 상태:**\n"
                for app in appliance_states:
                    status = "켜짐" if app.get("is_on") else "꺼짐"
                    prompt += f"- {app['appliance_type']}: {status}"
                    if app.get("is_on") and app.get("current_settings"):
                        prompt += f" (설정: {app['current_settings']})"
                    prompt += "\n"

            # 선호 세팅 사용 시 추가 지침
            preference_note = ""
            if has_preference_settings:
                preference_note = f"""
**중요: 학습된 선호 세팅 사용**
- "[학습된 선호 세팅]" 표시가 있는 가전은 **반드시 "지난번 설정하셨던"이나 "선호하시는"과 같은 표현**을 사용하세요
- 사용자가 이전에 학습한 설정임을 명확히 알려주세요
- 피로도 레벨 {fatigue_level}에 최적화된 설정임을 언급해도 좋습니다

**선호 세팅 사용 예시:**
- "지난번에 설정하셨던 23도 냉방 모드로 에어컨을 켜드릴까요?"
- "선호하시는 습도 50%로 가습기를 켜드릴까요?"
- "평소 설정하셨던 자동 모드로 공기청정기를 켜드릴까요?"
"""

            prompt += f"""
위 정보를 바탕으로 사용자에게 자연스럽게 가전 제어를 제안하는 메시지를 생성하세요.
{preference_note}
**기본 규칙:**
1. **반드시 구체적인 설정값을 포함**하여 제안하세요
   - 온도(target_temp_c): "23도로"
   - 습도(target_humidity_pct): "습도 50%로"
   - 모드(mode): "냉방 모드로", "자동 모드로"
   - 밝기(brightness_pct): "밝기 80%로"
2. 위에 나열된 등록된 가전만 언급하세요
3. 등록되지 않은 가전은 절대 언급하지 마세요
4. 현재 상황(온도, 습도 등)을 간단히 언급하여 제안 이유를 설명하세요

**좋은 예시 (일반):**
- "현재 온도가 28도로 높네요. 에어컨을 23도 냉방 모드로 켜드릴까요?"
- "습도가 30%로 건조하네요. 가습기를 습도 50% 자동 모드로 켜드릴까요?"
- "미세먼지가 80㎍/㎥로 나쁨 상태예요. 공기청정기를 자동 모드로 켜드릴까요?"

**나쁜 예시 (절대 하지 마세요):**
- "에어컨을 틀어드릴게요" (설정값 누락)
- "가습기를 켜드릴까요?" (목표 습도 누락)
- "공기청정기 켤까요?" (모드 누락)

반드시 일반 텍스트로만 응답하세요 (JSON 아님).
"""

            # 시스템 프롬프트 생성 (JSON 응답 지시 제거)
            system_prompt = f"""당신은 사용자의 스마트홈 AI 어시스턴트입니다.
사용자에게 자연스럽고 친근하게 대화하세요.
**중요: 일반 텍스트로만 응답하세요. JSON 형식을 사용하지 마세요.**
"""
            if persona:
                system_prompt += f"\n**말투/성격:**\n{persona.get('description', '')}\n"

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )

            suggestion = response.choices[0].message.content.strip()
            logger.info(f"✅ Suggestion generated: {suggestion[:50]}...")
            return suggestion

        except Exception as e:
            logger.error(f"❌ Suggestion generation error: {str(e)}")
            # Fallback
            appliance_names = [a["appliance_type"] for a in appliances]
            return f"현재 날씨와 피로도를 고려해서 {', '.join(appliance_names)}을(를) 켜드릴까요?"

    async def detect_modification(
        self,
        original_plan: Dict[str, Any],
        user_response: str
    ) -> Dict[str, Any]:
        """
        사용자 수정 사항 감지 (시나리오 2용)

        예:
        - "에어컨은 24도로" → {"에어컨": {"target_temp_c": 24}}
        - "공기청정기는 끄고" → {"공기청정기": {"action": "off"}}
        - "그대로 해줘" → {}

        Args:
            original_plan: 원래 제안했던 가전 제어 계획
            user_response: 사용자 응답

        Returns:
            {
                "has_modification": true/false,
                "modifications": {
                    "에어컨": {"target_temp_c": 24},
                    "공기청정기": {"action": "off"}
                },
                "approved": true/false
            }
        """
        try:
            appliances_str = json.dumps([
                {
                    "appliance_type": a["appliance_type"],
                    "settings": a.get("settings", {})
                }
                for a in original_plan.get("appliances", [])
            ], ensure_ascii=False, indent=2)

            prompt = f"""원래 제안:
{appliances_str}

사용자 응답: "{user_response}"

사용자가 수정을 요청했는지, 그대로 승인했는지, 거부했는지 판단하세요.

다음 JSON 형식으로 응답하세요:
{{
  "approved": true/false,
  "has_modification": true/false,
  "modifications": {{
    "가전종류": {{"설정키": 값}}
  }},
  "reason": "판단 이유"
}}

**예시:**
- "좋아", "그래", "응" → approved: true, has_modification: false
- "에어컨은 24도로" → approved: true, has_modification: true, modifications: {{"에어컨": {{"target_temp_c": 24}}}}
- "공기청정기는 끄고" → approved: true, has_modification: true, modifications: {{"공기청정기": {{"action": "off"}}}}
- "아니야", "괜찮아" → approved: false
"""

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 사용자 응답 분석 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            logger.info(f"✅ Modification detected: approved={result.get('approved')}, has_mod={result.get('has_modification')}")
            return result

        except Exception as e:
            logger.error(f"❌ Modification detection error: {str(e)}")
            return {
                "approved": True,
                "has_modification": False,
                "modifications": {},
                "reason": "파싱 실패 - 원래 계획 실행"
            }


class MemoryService:
    """대화 메모리 관리"""

    def __init__(self):
        # 실제로는 DB에 저장해야 함
        from collections import OrderedDict
        from datetime import datetime, timedelta

        self.short_term_memory: OrderedDict[str, List[Dict]] = OrderedDict()
        self.long_term_memory: OrderedDict[str, Dict] = OrderedDict()

        # 메모리 제한 설정
        self.MAX_USERS = 200  # 최대 사용자 수
        self.MAX_MESSAGES_PER_USER = 50  # 사용자당 최대 메시지 수
        self.MEMORY_TIMEOUT = timedelta(hours=6)  # 6시간 동안 접근 없으면 삭제
        self.last_access: Dict[str, datetime] = {}

    def _cleanup_old_memories(self):
        """오래된 메모리 정리"""
        from datetime import datetime
        now = datetime.now()
        to_delete = []

        for user_id in list(self.short_term_memory.keys()):
            last_time = self.last_access.get(user_id, now)
            if now - last_time > self.MEMORY_TIMEOUT:
                to_delete.append(user_id)

        for user_id in to_delete:
            self.short_term_memory.pop(user_id, None)
            self.long_term_memory.pop(user_id, None)
            self.last_access.pop(user_id, None)
            logger.info(f"🗑️ Cleaned up memory for user: {user_id}")

        # 최대 사용자 수 초과 시 오래된 것부터 삭제 (LRU)
        while len(self.short_term_memory) > self.MAX_USERS:
            oldest_user = next(iter(self.short_term_memory))
            self.short_term_memory.pop(oldest_user, None)
            self.long_term_memory.pop(oldest_user, None)
            self.last_access.pop(oldest_user, None)
            logger.info(f"🗑️ Evicted memory (max limit): {oldest_user}")

    def add_message(self, user_id: str, role: str, content: str):
        """대화 히스토리에 메시지 추가"""
        from datetime import datetime
        import random

        # 10% 확률로 정리 실행
        if random.random() < 0.1:
            self._cleanup_old_memories()

        if user_id not in self.short_term_memory:
            self.short_term_memory[user_id] = []

        self.short_term_memory[user_id].append({
            "role": role,
            "content": content
        })

        # 최근 메시지만 유지
        if len(self.short_term_memory[user_id]) > self.MAX_MESSAGES_PER_USER:
            self.short_term_memory[user_id] = self.short_term_memory[user_id][-self.MAX_MESSAGES_PER_USER:]

        # 접근 시간 갱신 (LRU)
        self.last_access[user_id] = datetime.now()
        # OrderedDict에서 최신 항목으로 이동
        if user_id in self.short_term_memory:
            self.short_term_memory.move_to_end(user_id)

    def get_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """대화 히스토리 조회"""
        from datetime import datetime

        if user_id not in self.short_term_memory:
            return []

        # 접근 시간 갱신
        self.last_access[user_id] = datetime.now()
        self.short_term_memory.move_to_end(user_id)

        return self.short_term_memory[user_id][-limit:]

    def update_long_term_memory(self, user_id: str, key: str, value: Any):
        """장기 메모리 업데이트"""
        from datetime import datetime

        if user_id not in self.long_term_memory:
            self.long_term_memory[user_id] = {}

        self.long_term_memory[user_id][key] = value

        # 접근 시간 갱신
        self.last_access[user_id] = datetime.now()
        if user_id in self.long_term_memory:
            self.long_term_memory.move_to_end(user_id)

    def get_long_term_memory(self, user_id: str) -> Dict:
        """장기 메모리 조회"""
        from datetime import datetime

        if user_id in self.last_access:
            self.last_access[user_id] = datetime.now()
        if user_id in self.long_term_memory:
            self.long_term_memory.move_to_end(user_id)

        return self.long_term_memory.get(user_id, {})


# 싱글톤 인스턴스
llm_service = LLMService()
memory_service = MemoryService()
