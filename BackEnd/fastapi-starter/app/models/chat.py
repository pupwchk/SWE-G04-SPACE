# app/models/chat.py
"""
채팅 세션 및 메시지 모델
사용자와 AI(페르소나)의 대화 내역을 저장
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.db import Base


class ChatSession(Base):
    """
    채팅 세션

    - 사용자별로 여러 세션을 가질 수 있음
    - 각 세션은 특정 페르소나와 연결 가능
    - 세션별로 대화 메시지들을 그룹화
    """
    __tablename__ = "chat_sessions"
    __table_args__ = (
        Index("ix_chat_sessions_user_id", "user_id"),
        Index("ix_chat_sessions_persona_id", "persona_id"),
        Index("ix_chat_sessions_last_message_at", "last_message_at"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Supabase 페르소나 ID (또는 FastAPI Character ID)
    # 문자열로 저장 (Supabase UUID는 외부 시스템)
    persona_id = Column(String, nullable=True)
    persona_nickname = Column(String, nullable=True)  # 캐싱용

    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    last_message_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    user = relationship("User", backref="chat_sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    """
    채팅 메시지

    - 사용자 메시지, AI 응답, 시스템 메시지 등을 저장
    - 가전 제어 관련 메타데이터 포함 (의도, 제안, 실행 결과)
    """
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_messages_session_id", "session_id"),
        Index("ix_chat_messages_created_at", "created_at"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 'user' | 'assistant' | 'system'
    role = Column(String, nullable=False)

    # 메시지 내용
    content = Column(Text, nullable=False)

    # 메타데이터 (시나리오 2용)
    intent_type = Column(String, nullable=True)  # environment_complaint, appliance_request, general_chat
    needs_control = Column(Boolean, nullable=True)

    # 가전 제어 관련 (JSONB)
    suggestions = Column(JSONB, nullable=True)  # 제안한 가전 제어 목록
    execution_results = Column(JSONB, nullable=True)  # 실행 결과

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    session = relationship("ChatSession", back_populates="messages")