"""
가전 제어 서비스 (가상 제어)
실제 가전 제어는 추후 IoT 통합 시 구현
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.appliance import ApplianceStatus, ApplianceCommandLog
from app.utils.appliance_mapping import (
    validate_settings,
    format_settings_for_frontend,
    format_appliance_status_for_frontend
)

logger = logging.getLogger(__name__)


class ApplianceControlService:
    """가전 제어 서비스 (가상)"""

    @staticmethod
    def execute_command(
        db: Session,
        user_id: str,
        appliance_type: str,
        action: str,
        settings: Optional[Dict[str, Any]] = None,
        triggered_by: str = "manual",
        fatigue_level_used: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        가전 제어 명령 실행 (가상)

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            appliance_type: 가전 종류
            action: 동작 (on/off/set)
            settings: 설정값
            triggered_by: 트리거 소스 (scenario1/scenario2/manual)
            fatigue_level_used: 사용된 피로도 레벨

        Returns:
            실행 결과
        """
        try:
            logger.info(f"🎛️ Executing command: {action} {appliance_type} for user {user_id}")

            # 설정값 검증
            if settings:
                is_valid, error = validate_settings(appliance_type, settings)
                if not is_valid:
                    logger.error(f"❌ Invalid settings: {error}")
                    return {
                        "success": False,
                        "appliance_type": appliance_type,
                        "action": action,
                        "error_message": error
                    }

            # 가상 제어 시뮬레이션
            success = True
            error_message = None

            # 가전 상태 업데이트
            status = db.query(ApplianceStatus)\
                .filter(
                    ApplianceStatus.user_id == user_id,
                    ApplianceStatus.appliance_type == appliance_type
                )\
                .first()

            if not status:
                # 새로운 상태 생성
                status = ApplianceStatus(
                    user_id=user_id,
                    appliance_type=appliance_type,
                    is_on=False,
                    current_settings={}
                )
                db.add(status)

            # 상태 업데이트
            if action == "on":
                status.is_on = True
                # 프론트엔드 포맷으로 설정값 저장
                status.current_settings = format_settings_for_frontend(
                    appliance_type, settings or {}
                )
                status.last_command = {
                    "action": action,
                    "settings": settings,
                    "timestamp": datetime.now().isoformat()
                }
            elif action == "off":
                status.is_on = False
                status.last_command = {
                    "action": action,
                    "timestamp": datetime.now().isoformat()
                }
            elif action == "set":
                if status.is_on:
                    # 기존 설정에 새 설정 병합
                    updated_settings = {**status.current_settings, **settings}
                    status.current_settings = format_settings_for_frontend(
                        appliance_type, updated_settings
                    )
                    status.last_command = {
                        "action": action,
                        "settings": settings,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    success = False
                    error_message = "Cannot set settings when appliance is off"

            # 명령 로그 저장
            command_log = ApplianceCommandLog(
                user_id=user_id,
                appliance_type=appliance_type,
                action=action,
                settings=settings,
                success=success,
                error_message=error_message,
                triggered_by=triggered_by,
                fatigue_level_used=fatigue_level_used
            )
            db.add(command_log)

            db.commit()
            db.refresh(status)

            if success:
                logger.info(f"✅ Command executed successfully: {appliance_type} is now {action}")
            else:
                logger.error(f"❌ Command failed: {error_message}")

            return {
                "success": success,
                "appliance_type": appliance_type,
                "action": action,
                "settings": settings,
                "current_state": {
                    "is_on": status.is_on,
                    "settings": status.current_settings
                },
                "error_message": error_message
            }

        except Exception as e:
            logger.error(f"❌ Command execution error: {str(e)}")

            # 실패 로그 저장
            command_log = ApplianceCommandLog(
                user_id=user_id,
                appliance_type=appliance_type,
                action=action,
                settings=settings,
                success=False,
                error_message=str(e),
                triggered_by=triggered_by,
                fatigue_level_used=fatigue_level_used
            )
            db.add(command_log)
            db.commit()

            return {
                "success": False,
                "appliance_type": appliance_type,
                "action": action,
                "error_message": str(e)
            }

    @staticmethod
    def execute_multiple_commands(
        db: Session,
        user_id: str,
        commands: list[Dict[str, Any]],
        triggered_by: str = "scenario1"
    ) -> list[Dict[str, Any]]:
        """
        여러 가전 제어 명령 일괄 실행

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            commands: 명령 리스트
                [
                    {
                        "appliance_type": "에어컨",
                        "action": "on",
                        "settings": {...},
                        "fatigue_level": 3
                    },
                    ...
                ]
            triggered_by: 트리거 소스

        Returns:
            실행 결과 리스트
        """
        results = []

        for cmd in commands:
            result = ApplianceControlService.execute_command(
                db=db,
                user_id=user_id,
                appliance_type=cmd["appliance_type"],
                action=cmd.get("action", "on"),
                settings=cmd.get("settings"),
                triggered_by=triggered_by,
                fatigue_level_used=cmd.get("fatigue_level")
            )
            results.append(result)

        return results

    @staticmethod
    def get_appliance_status(
        db: Session,
        user_id: str,
        appliance_type: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        가전 상태 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            appliance_type: 가전 종류 (None이면 전체 조회)

        Returns:
            가전 상태 리스트
        """
        query = db.query(ApplianceStatus)\
            .filter(ApplianceStatus.user_id == user_id)

        if appliance_type:
            query = query.filter(ApplianceStatus.appliance_type == appliance_type)

        statuses = query.all()

        return [
            format_appliance_status_for_frontend(
                appliance_type=status.appliance_type,
                is_on=status.is_on,
                current_settings=status.current_settings,
                last_command=status.last_command,
                last_updated=status.last_updated.isoformat()
            )
            for status in statuses
        ]

    @staticmethod
    def get_command_history(
        db: Session,
        user_id: str,
        limit: int = 20
    ) -> list[Dict[str, Any]]:
        """
        가전 제어 히스토리 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            limit: 조회 개수

        Returns:
            명령 히스토리 리스트
        """
        from sqlalchemy import desc

        logs = db.query(ApplianceCommandLog)\
            .filter(ApplianceCommandLog.user_id == user_id)\
            .order_by(desc(ApplianceCommandLog.executed_at))\
            .limit(limit)\
            .all()

        return [
            {
                "appliance_type": log.appliance_type,
                "action": log.action,
                "settings": log.settings,
                "success": log.success,
                "error_message": log.error_message,
                "triggered_by": log.triggered_by,
                "fatigue_level_used": log.fatigue_level_used,
                "executed_at": log.executed_at.isoformat()
            }
            for log in logs
        ]


# 싱글톤 인스턴스
appliance_control_service = ApplianceControlService()
