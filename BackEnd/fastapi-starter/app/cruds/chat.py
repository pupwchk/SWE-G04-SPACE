# app/cruds/chat.py
"""
채팅 세션 및 메시지 CRUD 연산
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.chat import ChatSession, ChatMessage


def get_or_create_session(
    db: Session,
    user_id: UUID,
    persona_id: Optional[str] = None,
    persona_nickname: Optional[str] = None
) -> ChatSession:
    """
    활성 세션 조회 또는 새 세션 생성

    - 같은 user_id + persona_id 조합의 활성 세션이 있으면 재사용
    - 없으면 새로 생성
    """
    # 활성 세션 조회
    session = db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.persona_id == persona_id,
        ChatSession.is_active == True
    ).order_by(desc(ChatSession.last_message_at)).first()

    if session:
        # 기존 세션의 last_message_at 갱신
        session.last_message_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    # 새 세션 생성
    new_session = ChatSession(
        user_id=user_id,
        persona_id=persona_id,
        persona_nickname=persona_nickname
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


def save_message(
    db: Session,
    session_id: UUID,
    role: str,
    content: str,
    intent_type: Optional[str] = None,
    needs_control: Optional[bool] = None,
    suggestions: Optional[List[Dict[str, Any]]] = None,
    execution_results: Optional[List[Dict[str, Any]]] = None
) -> ChatMessage:
    """
    채팅 메시지 저장

    Args:
        session_id: 세션 ID
        role: 'user' | 'assistant' | 'system'
        content: 메시지 내용
        intent_type: 의도 유형 (environment_complaint, appliance_request, general_chat)
        needs_control: 가전 제어 필요 여부
        suggestions: 가전 제어 제안 목록
        execution_results: 가전 제어 실행 결과
    """
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        intent_type=intent_type,
        needs_control=needs_control,
        suggestions=suggestions,
        execution_results=execution_results
    )

    db.add(message)

    # 세션의 last_message_at 갱신
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        session.last_message_at = datetime.utcnow()

    db.commit()
    db.refresh(message)
    return message


def get_session_messages(
    db: Session,
    session_id: UUID,
    limit: int = 50
) -> List[ChatMessage]:
    """
    세션의 메시지 목록 조회 (최근 순)
    """
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).limit(limit).all()

    return messages


def get_user_sessions(
    db: Session,
    user_id: UUID,
    limit: int = 10,
    active_only: bool = False
) -> List[ChatSession]:
    """
    사용자의 세션 목록 조회 (최근 순)
    """
    query = db.query(ChatSession).filter(ChatSession.user_id == user_id)

    if active_only:
        query = query.filter(ChatSession.is_active == True)

    sessions = query.order_by(desc(ChatSession.last_message_at)).limit(limit).all()
    return sessions


def close_session(db: Session, session_id: UUID) -> bool:
    """
    세션 비활성화
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

    if not session:
        return False

    session.is_active = False
    db.commit()
    return True


def delete_session(db: Session, session_id: UUID) -> bool:
    """
    세션 삭제 (메시지도 함께 cascade 삭제)
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

    if not session:
        return False

    db.delete(session)
    db.commit()
    return True
