#!/usr/bin/env python3
"""
SendBird Calls AI Assistant 수동 등록 스크립트

AI assistant(home_ai_assistant)를 SendBird Calls에 수동으로 등록합니다.
백엔드 서버가 자동으로 등록하므로, 보통은 이 스크립트를 실행할 필요가 없습니다.

Usage:
    cd BackEnd/fastapi-starter
    python scripts/register_ai_sendbird_calls.py
"""

import sys
import asyncio
import logging
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.sendbird_client import SendbirdCallsClient
from app.config.sendbird import SendbirdConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """AI assistant를 SendBird Calls에 등록"""
    logger.info("=" * 80)
    logger.info("🚀 SendBird Calls AI Assistant 등록 시작")
    logger.info("=" * 80)

    # 설정 정보 출력
    logger.info(f"📋 설정 정보:")
    logger.info(f"   APP_ID: {SendbirdConfig.APP_ID}")
    logger.info(f"   AI_USER_ID: {SendbirdConfig.AI_USER_ID}")
    logger.info(f"   AI_USER_NAME: {SendbirdConfig.AI_USER_NAME}")
    logger.info(f"   CALLS_API_BASE: {SendbirdConfig.CALLS_API_BASE}")

    # SendBird Calls 클라이언트 생성
    calls_client = SendbirdCallsClient()

    try:
        # AI assistant 등록
        logger.info("\n🔧 AI assistant 등록 중...")
        result = await calls_client.register_ai_assistant()

        logger.info("\n✅ 등록 완료!")
        logger.info(f"   결과: {result}")

        logger.info("\n" + "=" * 80)
        logger.info("🎉 모든 작업이 성공적으로 완료되었습니다!")
        logger.info("=" * 80)
        logger.info("\n다음 단계:")
        logger.info("1. iOS 앱에서 페르소나 채팅 화면으로 이동")
        logger.info("2. 우측 상단 전화 아이콘 탭")
        logger.info("3. AI assistant에게 전화 연결 시도")
        logger.info("4. 성공 시 PhoneCallView 표시")

    except Exception as e:
        logger.error("\n❌ 등록 실패!")
        logger.error(f"   에러: {str(e)}")
        logger.error("\n문제 해결:")
        logger.error("1. 환경 변수 확인:")
        logger.error("   - SENDBIRD_APP_ID")
        logger.error("   - SENDBIRD_API_TOKEN")
        logger.error("2. SendBird Dashboard에서 API Token 권한 확인")
        logger.error("3. 네트워크 연결 확인")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
