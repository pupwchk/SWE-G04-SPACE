"""
Supabase 페르소나 시스템 연동 서비스
사용자가 선택한 페르소나를 Supabase에서 조회하여 LLM에 적용
"""
import os
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID

logger = logging.getLogger(__name__)


class SupabasePersonaService:
    """
    Supabase 페르소나 시스템 연동

    기능:
    - 페르소나 조회 (adjectives 포함)
    - 사용자 선택 페르소나 목록 조회
    - final_prompt 생성 (adjectives + custom_instructions 병합)
    """

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "")
        # SERVICE_ROLE_KEY 사용 (RLS 우회 가능)
        # 백엔드에서만 사용하므로 안전함
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")
        self.client = None

        # Supabase 클라이언트 초기화
        if self.url and self.key:
            try:
                from supabase import create_client, Client
                self.client: Client = create_client(self.url, self.key)
                key_type = "SERVICE_ROLE" if os.getenv("SUPABASE_SERVICE_ROLE_KEY") else "ANON"
                logger.info(f"✅ Supabase client initialized with {key_type} key")
            except ImportError:
                logger.warning("⚠️ supabase-py not installed. Run: pip install supabase")
            except Exception as e:
                logger.error(f"❌ Supabase initialization error: {str(e)}")
        else:
            logger.warning("⚠️ SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")

    def is_available(self) -> bool:
        """Supabase 사용 가능 여부"""
        return self.client is not None

    def get_persona(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """
        단일 페르소나 조회 (adjectives 포함)

        Args:
            persona_id: 페르소나 ID

        Returns:
            {
                "id": "uuid",
                "user_id": "uuid",
                "nickname": "친절한 비서",
                "adjective_ids": ["uuid1", "uuid2"],
                "custom_instructions": "...",
                "final_prompt": "...",
                "adjectives": [
                    {
                        "id": "uuid1",
                        "adjective_name": "친근한",
                        "instruction_text": "친구처럼 편안하고 따뜻한 어조로 답변합니다.",
                        "category": "스타일"
                    },
                    ...
                ]
            }
        """
        if not self.is_available():
            logger.warning("⚠️ Supabase not available, returning None")
            return None

        try:
            # 페르소나 조회 (adjectives join)
            result = self.client.table("personas")\
                .select("*")\
                .eq("id", persona_id)\
                .single()\
                .execute()

            if not result.data:
                logger.warning(f"⚠️ Persona not found: {persona_id}")
                return None

            persona_data = result.data

            # adjectives 조회 (adjective_ids 배열 기반)
            adjective_ids = persona_data.get("adjective_ids", [])
            adjectives = []

            if adjective_ids:
                adj_result = self.client.table("adjectives")\
                    .select("*")\
                    .in_("id", adjective_ids)\
                    .execute()

                adjectives = adj_result.data if adj_result.data else []

            persona_data["adjectives"] = adjectives

            logger.info(f"✅ Persona loaded: {persona_data['nickname']} with {len(adjectives)} adjectives")
            return persona_data

        except Exception as e:
            logger.error(f"❌ Error fetching persona {persona_id}: {str(e)}")
            return None

    def get_user_selected_personas(self, email: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        사용자가 선택한 페르소나 목록 조회 (최대 5개)

        ⚠️ 중요: Supabase의 user_id는 Supabase Auth UUID이므로,
        FastAPI의 PostgreSQL user_id와 다릅니다.
        이 함수는 email을 받아서 Supabase에서 user_id를 찾은 후 조회합니다.

        Args:
            email: 사용자 이메일 (Supabase와 PostgreSQL 모두에서 동일)
            limit: 조회 개수 (기본 5)

        Returns:
            [
                {
                    "id": "uuid",
                    "user_id": "uuid",  # Supabase Auth UUID
                    "persona_id": "uuid",
                    "selection_order": 1,
                    "persona": {
                        "id": "uuid",
                        "nickname": "친절한 비서",
                        "adjective_ids": [...],
                        "custom_instructions": "...",
                        "final_prompt": "...",
                        "adjectives": [...]
                    }
                },
                ...
            ]
        """
        if not self.is_available():
            logger.warning("⚠️ Supabase not available, returning empty list")
            return []

        try:
            # 1. email로 Supabase user_id 찾기 (Supabase Auth UUID)
            # Supabase의 auth.users는 직접 조회 불가능하므로,
            # profiles 또는 users 테이블에서 email로 user_id를 찾음
            supabase_user_id = None

            # 방법 1: Auth Admin API 사용 (권한이 있는 경우)
            try:
                # Note: Admin API는 service_role key가 필요할 수 있음
                # 현재는 anon key를 사용하므로 실패 가능
                logger.debug(f"🔍 [SUPABASE-PERSONA] Trying to find user_id for email: {email}")
            except Exception as e:
                logger.debug(f"ℹ️ [SUPABASE-PERSONA] Auth Admin API not available: {str(e)}")

            # 방법 2: users 테이블에서 email로 조회 (우선순위)
            try:
                user_result = self.client.table("users")\
                    .select("id, email")\
                    .eq("email", email)\
                    .execute()

                if user_result.data:
                    # 결과 확인 - data가 리스트인 경우와 단일 객체인 경우 모두 처리
                    if isinstance(user_result.data, list) and len(user_result.data) > 0:
                        supabase_user_id = user_result.data[0].get("id")
                    elif isinstance(user_result.data, dict):
                        supabase_user_id = user_result.data.get("id")

                    if supabase_user_id:
                        logger.debug(f"✅ [SUPABASE-PERSONA] Found user_id via users table: {supabase_user_id}")
            except Exception as e:
                logger.debug(f"ℹ️ [SUPABASE-PERSONA] Users table query failed: {str(e)}")

            # 방법 3: profiles 테이블에서 email로 조회 (fallback)
            if not supabase_user_id:
                try:
                    profile_result = self.client.table("profiles")\
                        .select("id, email")\
                        .eq("email", email)\
                        .execute()

                    if profile_result.data:
                        if isinstance(profile_result.data, list) and len(profile_result.data) > 0:
                            supabase_user_id = profile_result.data[0].get("id")
                        elif isinstance(profile_result.data, dict):
                            supabase_user_id = profile_result.data.get("id")

                        if supabase_user_id:
                            logger.debug(f"✅ [SUPABASE-PERSONA] Found user_id via profiles: {supabase_user_id}")
                except Exception as e:
                    logger.debug(f"ℹ️ [SUPABASE-PERSONA] Profiles query failed: {str(e)}")

            if not supabase_user_id:
                logger.warning(f"⚠️ [SUPABASE-PERSONA] Could not find Supabase user_id for email: {email}")
                return []

            # 2. 선택된 페르소나 목록 조회 (Supabase user_id 사용)
            result = self.client.table("user_selected_personas")\
                .select("*, personas(*)")\
                .eq("user_id", supabase_user_id)\
                .order("selection_order")\
                .limit(limit)\
                .execute()

            if not result.data:
                logger.info(f"ℹ️ No selected personas for email {email} (Supabase user_id: {supabase_user_id})")
                return []

            selected_personas = result.data

            # 각 페르소나의 adjectives 로드
            for item in selected_personas:
                persona_data = item.get("personas", {})
                if persona_data:
                    adjective_ids = persona_data.get("adjective_ids", [])
                    adjectives = []

                    if adjective_ids:
                        adj_result = self.client.table("adjectives")\
                            .select("*")\
                            .in_("id", adjective_ids)\
                            .execute()

                        adjectives = adj_result.data if adj_result.data else []

                    persona_data["adjectives"] = adjectives
                    item["persona"] = persona_data

            logger.info(f"✅ Loaded {len(selected_personas)} selected personas for email {email}")
            return selected_personas

        except Exception as e:
            logger.error(f"❌ Error fetching selected personas for email {email}: {str(e)}")
            return []

    def build_final_prompt(self, persona_data: Dict[str, Any]) -> str:
        """
        페르소나의 final_prompt 생성

        Args:
            persona_data: get_persona() 결과

        Returns:
            병합된 프롬프트 문자열
        """
        # 1. DB에 저장된 final_prompt가 있으면 우선 사용
        if persona_data.get("final_prompt"):
            return persona_data["final_prompt"]

        # 2. adjectives + custom_instructions 병합
        adjectives = persona_data.get("adjectives", [])
        custom = persona_data.get("custom_instructions", "")

        # adjectives를 instruction_text로 병합
        adjective_texts = []
        for adj in adjectives:
            category = adj.get("category", "일반")
            name = adj.get("adjective_name", "")
            instruction = adj.get("instruction_text", "")
            adjective_texts.append(f"[{category}] {name}: {instruction}")

        # 최종 프롬프트 생성
        parts = []

        if adjective_texts:
            parts.append("## 선택된 특성:")
            parts.extend(adjective_texts)

        if custom:
            parts.append("\n## 추가 지침:")
            parts.append(custom)

        final_prompt = "\n".join(parts) if parts else "기본 페르소나"

        logger.info(f"✅ Built final_prompt for {persona_data.get('nickname', 'Unknown')}: {len(final_prompt)} chars")
        return final_prompt

    def get_persona_for_llm(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """
        LLM에 바로 사용 가능한 페르소나 정보 반환

        Args:
            persona_id: 페르소나 ID

        Returns:
            {
                "nickname": "친절한 비서",
                "description": "친구처럼 편안하고 따뜻한 어조로 답변합니다. ..."
            }
            또는 None
        """
        persona_data = self.get_persona(persona_id)

        if not persona_data:
            return None

        final_prompt = self.build_final_prompt(persona_data)

        return {
            "nickname": persona_data.get("nickname", "Unknown"),
            "description": final_prompt
        }


# 싱글톤 인스턴스
supabase_persona_service = SupabasePersonaService()
