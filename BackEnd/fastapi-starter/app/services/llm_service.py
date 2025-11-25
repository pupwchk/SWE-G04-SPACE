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
