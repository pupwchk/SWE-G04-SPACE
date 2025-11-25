# app/api/characters.py

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.db import get_db
import app.schemas.info as infoSchema
import app.cruds.info as infoCruds

router = APIRouter()


# -----------------------------
# Characters
# -----------------------------

@router.get("/user/{user_id}", response_model=list[infoSchema.Character])
def get_characters_by_user(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """특정 유저의 캐릭터 리스트 조회"""
    characters = infoCruds.get_characters_by_user(
        db,
        user_id=user_id,
        skip=skip,
        limit=limit,
    )
    return characters


@router.post(
    "/",
    response_model=infoSchema.Character,
    status_code=status.HTTP_201_CREATED,
)
def create_character(
    character: infoSchema.CharacterCreate,
    db: Session = Depends(get_db),
):
    """캐릭터 생성"""
    return infoCruds.create_character(db, character)


@router.get("/{character_id}", response_model=infoSchema.Character)
def get_character(
    character_id: UUID,
    db: Session = Depends(get_db),
):
    """단일 캐릭터 조회"""
    db_character = infoCruds.get_character(db, character_id=character_id)
    if not db_character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )
    return db_character


@router.patch("/{character_id}", response_model=infoSchema.Character)
def update_character(
    character_id: UUID,
    payload: infoSchema.CharacterUpdate,
    db: Session = Depends(get_db),
):
    """캐릭터 정보 수정 (nickname / persona)"""
    db_character = infoCruds.update_character(
        db,
        character_id=character_id,
        character_in=payload,
    )
    if not db_character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )
    return db_character


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character(
    character_id: UUID,
    db: Session = Depends(get_db),
):
    """캐릭터 삭제"""
    ok = infoCruds.delete_character(db, character_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )
    return None
