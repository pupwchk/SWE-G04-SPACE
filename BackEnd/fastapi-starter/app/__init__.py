import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

# 환경 변수로 로깅 레벨 설정 (기본값: INFO)
# LOG_LEVEL=DEBUG (개발), LOG_LEVEL=WARNING (프로덕션)
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 앱 시작/종료 시 실행되는 이벤트"""
    logger.info("✅ FastAPI app starting up...")

    yield

    # 종료 시 정리 작업 (필요시)
    logger.info("🔄 FastAPI app shutting down...")


app = FastAPI(lifespan=lifespan)