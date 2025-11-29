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
        self.key = os.getenv("SUPABASE_ANON_KEY", "")
        self.client = None

        # Supabase 클라이언트 초기화
        if self.url and self.key:
            try:
                from supabase import create_client, Client
                self.client: Client = create_client(self.url, self.key)
                logger.info("✅ Supabase client initialized")
            except ImportError:
                logger.warning("⚠️ supabase-py not installed. Run: pip install supabase")
            except Exception as e:
                logger.error(f"❌ Supabase initialization error: {str(e)}")
        else:
            logger.warning("⚠️ SUPABASE_URL or SUPABASE_ANON_KEY not set")

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

    def get_user_selected_personas(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        사용자가 선택한 페르소나 목록 조회 (최대 5개)

        Args:
            user_id: 사용자 ID
            limit: 조회 개수 (기본 5)

        Returns:
            [
                {
                    "id": "uuid",
                    "user_id": "uuid",
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
            # 선택된 페르소나 목록 조회
            result = self.client.table("user_selected_personas")\
                .select("*, personas(*)")\
                .eq("user_id", user_id)\
                .order("selection_order")\
                .limit(limit)\
                .execute()

            if not result.data:
                logger.info(f"ℹ️ No selected personas for user {user_id}")
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

            logger.info(f"✅ Loaded {len(selected_personas)} selected personas for user {user_id}")
            return selected_personas

        except Exception as e:
            logger.error(f"❌ Error fetching selected personas for {user_id}: {str(e)}")
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
