import os
import logging
from fastapi import FastAPI

# 환경 변수로 로깅 레벨 설정 (기본값: INFO)
# LOG_LEVEL=DEBUG (개발), LOG_LEVEL=WARNING (프로덕션)
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))

app = FastAPI()