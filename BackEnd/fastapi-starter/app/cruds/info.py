# app/cruds/info.py

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.info import (
    Appliance,
    AirConditionerConfig,
    TvConfig,
    AirPurifierConfig,
    LightConfig,
    HumidifierConfig,
    Character,
)

from app.schemas.info import (
    ApplianceCreate,
    AirConditionerConfigCreate,
    TvConfigCreate,
    AirPurifierConfigCreate,
    LightConfigCreate,
    HumidifierConfigCreate,
    CharacterCreate,
    CharacterUpdate,
)

# ============================================================
# Appliance CRUD
# ============================================================

def create_appliance(
    db: Session,
    appliance_in: ApplianceCreate,
) -> Appliance:
    """
    가전(Appliance) 생성
    """
    db_obj = Appliance(**appliance_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_appliance(
    db: Session,
    appliance_id: UUID,
) -> Optional[Appliance]:
    """
    appliance_id로 단일 가전 조회
    """
    return (
        db.query(Appliance)
        .filter(Appliance.id == appliance_id)
        .first()
    )


def get_appliances_by_user(
    db: Session,
    user_id: UUID,
    appliance_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Appliance]:
    """
    특정 유저의 가전 목록 조회
      - appliance_code로 필터링 가능 (예: 'AC', 'TV', ...)
    """
    query = db.query(Appliance).filter(Appliance.user_id == user_id)

    if appliance_code is not None:
        query = query.filter(Appliance.appliance_code == appliance_code)

    return query.offset(skip).limit(limit).all()


def delete_appliance(
    db: Session,
    appliance_id: UUID,
) -> bool:
    """
    가전 삭제
      - 성공 시 True, 대상 없으면 False
    """
    db_obj = (
        db.query(Appliance)
        .filter(Appliance.id == appliance_id)
        .first()
    )
    if db_obj is None:
        return False

    db.delete(db_obj)
    db.commit()
    return True


# ============================================================
# Config 업서트(1:1) 헬퍼들
#   - 이미 있으면 UPDATE, 없으면 CREATE
# ============================================================

# ---------- AirConditionerConfig ----------

def upsert_air_conditioner_config(
    db: Session,
    cfg_in: AirConditionerConfigCreate,
) -> AirConditionerConfig:
    """
    에어컨 설정 업서트
      - appliance_id 기준 1:1
      - 존재하면 필드 업데이트, 없으면 새로 생성
    """
    db_obj = (
        db.query(AirConditionerConfig)
        .filter(AirConditionerConfig.appliance_id == cfg_in.appliance_id)
        .first()
    )

    data = cfg_in.model_dump()

    if db_obj is None:
        db_obj = AirConditionerConfig(**data)
        db.add(db_obj)
    else:
        for field, value in data.items():
            setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_air_conditioner_config_by_appliance(
    db: Session,
    appliance_id: UUID,
) -> Optional[AirConditionerConfig]:
    return (
        db.query(AirConditionerConfig)
        .filter(AirConditionerConfig.appliance_id == appliance_id)
        .first()
    )


# ---------- TvConfig ----------

def upsert_tv_config(
    db: Session,
    cfg_in: TvConfigCreate,
) -> TvConfig:
    """
    TV 설정 업서트
    """
    db_obj = (
        db.query(TvConfig)
        .filter(TvConfig.appliance_id == cfg_in.appliance_id)
        .first()
    )

    data = cfg_in.model_dump()

    if db_obj is None:
        db_obj = TvConfig(**data)
        db.add(db_obj)
    else:
        for field, value in data.items():
            setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_tv_config_by_appliance(
    db: Session,
    appliance_id: UUID,
) -> Optional[TvConfig]:
    return (
        db.query(TvConfig)
        .filter(TvConfig.appliance_id == appliance_id)
        .first()
    )


# ---------- AirPurifierConfig ----------

def upsert_air_purifier_config(
    db: Session,
    cfg_in: AirPurifierConfigCreate,
) -> AirPurifierConfig:
    """
    공기청정기 설정 업서트
    """
    db_obj = (
        db.query(AirPurifierConfig)
        .filter(AirPurifierConfig.appliance_id == cfg_in.appliance_id)
        .first()
    )

    data = cfg_in.model_dump()

    if db_obj is None:
        db_obj = AirPurifierConfig(**data)
        db.add(db_obj)
    else:
        for field, value in data.items():
            setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_air_purifier_config_by_appliance(
    db: Session,
    appliance_id: UUID,
) -> Optional[AirPurifierConfig]:
    return (
        db.query(AirPurifierConfig)
        .filter(AirPurifierConfig.appliance_id == appliance_id)
        .first()
    )


# ---------- LightConfig ----------

def upsert_light_config(
    db: Session,
    cfg_in: LightConfigCreate,
) -> LightConfig:
    """
    조명 설정 업서트
    """
    db_obj = (
        db.query(LightConfig)
        .filter(LightConfig.appliance_id == cfg_in.appliance_id)
        .first()
    )

    data = cfg_in.model_dump()

    if db_obj is None:
        db_obj = LightConfig(**data)
        db.add(db_obj)
    else:
        for field, value in data.items():
            setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_light_config_by_appliance(
    db: Session,
    appliance_id: UUID,
) -> Optional[LightConfig]:
    return (
        db.query(LightConfig)
        .filter(LightConfig.appliance_id == appliance_id)
        .first()
    )


# ---------- HumidifierConfig ----------

def upsert_humidifier_config(
    db: Session,
    cfg_in: HumidifierConfigCreate,
) -> HumidifierConfig:
    """
    가습기 설정 업서트
    """
    db_obj = (
        db.query(HumidifierConfig)
        .filter(HumidifierConfig.appliance_id == cfg_in.appliance_id)
        .first()
    )

    data = cfg_in.model_dump()

    if db_obj is None:
        db_obj = HumidifierConfig(**data)
        db.add(db_obj)
    else:
        for field, value in data.items():
            setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_humidifier_config_by_appliance(
    db: Session,
    appliance_id: UUID,
) -> Optional[HumidifierConfig]:
    return (
        db.query(HumidifierConfig)
        .filter(HumidifierConfig.appliance_id == appliance_id)
        .first()
    )


# ============================================================
# Character CRUD (User : Character = 1 : N)
# ============================================================

def create_character(
    db: Session,
    character_in: CharacterCreate,
) -> Character:
    """
    캐릭터 생성
    - user_id, nickname, persona를 받아 새 Character 레코드를 만든다.
    """
    db_obj = Character(**character_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_character(
    db: Session,
    character_id: UUID,
) -> Optional[Character]:
    """
    character_id로 캐릭터 단건 조회
    """
    return (
        db.query(Character)
        .filter(Character.id == character_id)
        .first()
    )


def get_characters_by_user(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> List[Character]:
    """
    특정 유저(user_id)의 캐릭터 리스트 조회
    """
    return (
        db.query(Character)
        .filter(Character.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_character(
    db: Session,
    character_id: UUID,
    character_in: CharacterUpdate,
) -> Optional[Character]:
    """
    캐릭터 정보 수정 (닉네임 / 페르소나 부분 업데이트)
    """
    db_obj = (
        db.query(Character)
        .filter(Character.id == character_id)
        .first()
    )
    if db_obj is None:
        return None

    update_data = character_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_character(
    db: Session,
    character_id: UUID,
) -> bool:
    """
    캐릭터 삭제
      - 삭제 성공 시 True, 대상 없으면 False
    """
    db_obj = (
        db.query(Character)
        .filter(Character.id == character_id)
        .first()
    )
    if db_obj is None:
        return False

    db.delete(db_obj)
    db.commit()
    return True
