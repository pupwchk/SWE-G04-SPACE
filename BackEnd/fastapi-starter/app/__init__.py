import logging
from fastapi import FastAPI

# 로깅 레벨을 INFO로 설정하여 모든 정보성 로그가 출력되도록 함
logging.basicConfig(level=logging.INFO)

app = FastAPI()