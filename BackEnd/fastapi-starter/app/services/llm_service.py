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
    CALL = "CALL"  # 사용자가 요청한 전화
    AUTO_CALL = "AUTO_CALL"  # GPS 기반 자동 전화


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
- 필요시 전화로 직접 대화 제안

**응답 형식:**
반드시 JSON 형식으로 응답하세요:

1. 일반 텍스트 응답:
{
  "action": "NONE",
  "response": "응답 메시지"
}

2. 전화 걸기 (사용자가 요청했을 때):
{
  "action": "CALL",
  "response": "전화 드릴게요!",
  "reason": "사용자 요청"
}

3. GPS 기반 자동 전화 (집 근처 도착 시):
{
  "action": "AUTO_CALL",
  "trigger": "GEO_FENCE",
  "response": "집에 거의 다 오셨네요. 필요한 게 있을까요?",
  "message_to_user": "잠시 후 전화 드릴게요."
}

**중요:**
- 항상 JSON만 반환하세요
- 사용자가 "전화해줘", "통화하자" 등을 말하면 action: "CALL"
- 일상적인 대화는 action: "NONE"
"""
        
        if persona:
            base_prompt += f"\n**말투/성격:**\n{persona.get('description', '')}\n"
        
        return base_prompt
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        persona: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        LLM 응답 생성
        
        Args:
            user_message: 사용자 메시지
            conversation_history: 대화 히스토리
            persona: 페르소나 정보
            context: 추가 컨텍스트 (위치, 시간, 상태 등)
        
        Returns:
            {
                "action": "NONE" | "CALL" | "AUTO_CALL",
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
    
    async def generate_geofence_trigger(
        self,
        user_id: str,
        distance: float,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Geofence 진입 시 자동 전화 트리거 생성
        
        Args:
            user_id: 사용자 ID
            distance: 집까지 거리 (미터)
            context: 추가 컨텍스트
        
        Returns:
            AUTO_CALL 액션
        """
        try:
            prompt = f"""사용자가 집에서 {distance:.0f}m 거리에 있습니다.
집에 거의 도착했으므로 자동으로 전화를 걸어 필요한 것이 있는지 물어보려고 합니다.

다음 JSON 형식으로 응답하세요:
{{
  "action": "AUTO_CALL",
  "trigger": "GEO_FENCE",
  "response": "집에 도착하기 전에 전화로 필요한 것을 물어볼 메시지",
  "message_to_user": "전화 걸기 전에 채팅으로 보낼 짧은 메시지"
}}
"""
            
            if context:
                prompt += f"\n\n추가 정보:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            logger.info(f"✅ Geofence trigger generated for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Geofence trigger error: {str(e)}")
            # Fallback
            return {
                "action": "AUTO_CALL",
                "trigger": "GEO_FENCE",
                "response": "집에 거의 다 오셨네요. 필요한 게 있을까요?",
                "message_to_user": "집에 거의 도착하셨어요. 잠시 후 전화 드릴게요."
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

    async def generate_appliance_suggestion(
        self,
        appliances: List[Dict[str, Any]],
        weather: Dict[str, Any],
        fatigue_level: int,
        user_message: str
    ) -> str:
        """
        가전 제어 제안 메시지 생성 (시나리오 2용)

        Args:
            appliances: 제어할 가전 목록
            weather: 날씨 데이터
            fatigue_level: 피로도 레벨
            user_message: 사용자 원본 메시지

        Returns:
            제안 메시지 (예: "현재 온도가 28도로 높고, 피로도가 3이에요. 에어컨을 23도로 켜고, 공기청정기도 켤까요?")
        """
        try:
            appliance_info = []
            for app in appliances:
                info = f"{app['appliance_type']}: {app['settings']}"
                if app.get('reason'):
                    info += f" ({app['reason']})"
                appliance_info.append(info)

            prompt = f"""사용자가 "{user_message}"라고 말했습니다.

**현재 상황:**
- 온도: {weather.get('temperature')}°C
- 습도: {weather.get('humidity')}%
- 미세먼지: {weather.get('pm10')} ㎍/㎥
- 피로도 레벨: {fatigue_level} (1:좋음, 2:보통, 3:나쁨, 4:매우나쁨)

**추천 가전 제어:**
{chr(10).join(appliance_info)}

위 정보를 바탕으로 사용자에게 자연스럽게 가전 제어를 제안하는 메시지를 생성하세요.
형식: "현재 [날씨 설명]. [가전 제어 제안]할까요?"
반드시 일반 텍스트로만 응답하세요 (JSON 아님).
"""

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 친근한 스마트홈 AI 어시스턴트입니다."},
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
        self.short_term_memory: Dict[str, List[Dict]] = {}
        self.long_term_memory: Dict[str, Dict] = {}
    
    def add_message(self, user_id: str, role: str, content: str):
        """대화 히스토리에 메시지 추가"""
        if user_id not in self.short_term_memory:
            self.short_term_memory[user_id] = []
        
        self.short_term_memory[user_id].append({
            "role": role,
            "content": content
        })
        
        # 최근 50개만 유지
        if len(self.short_term_memory[user_id]) > 50:
            self.short_term_memory[user_id] = self.short_term_memory[user_id][-50:]
    
    def get_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """대화 히스토리 조회"""
        if user_id not in self.short_term_memory:
            return []
        return self.short_term_memory[user_id][-limit:]
    
    def update_long_term_memory(self, user_id: str, key: str, value: Any):
        """장기 메모리 업데이트"""
        if user_id not in self.long_term_memory:
            self.long_term_memory[user_id] = {}
        
        self.long_term_memory[user_id][key] = value
    
    def get_long_term_memory(self, user_id: str) -> Dict:
        """장기 메모리 조회"""
        return self.long_term_memory.get(user_id, {})


# 싱글톤 인스턴스
llm_service = LLMService()
memory_service = MemoryService()
