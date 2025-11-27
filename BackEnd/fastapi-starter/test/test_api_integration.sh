#!/bin/bash

echo "========================================="
echo "FastAPI Integration Test"
echo "========================================="

BASE_URL="http://localhost:11325/api"

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 테스트 유저 ID (UUID)
USER_ID="123e4567-e89b-12d3-a456-426614174000"

echo ""
echo "========================================="
echo "1. HRV API 테스트"
echo "========================================="

# HRV 데이터 동기화
echo -e "${YELLOW}POST /health/hrv${NC}"
RESPONSE=$(curl -s -X POST "$BASE_URL/health/hrv" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "'$USER_ID'",
    "hrv_value": 35.5,
    "measured_at": "2025-11-26T14:00:00Z"
  }')

if echo "$RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✅ HRV 동기화 성공${NC}"
    echo "$RESPONSE" | jq .
else
    echo -e "${RED}❌ HRV 동기화 실패${NC}"
    echo "$RESPONSE"
fi

echo ""

# 피로도 조회
echo -e "${YELLOW}GET /health/fatigue/$USER_ID${NC}"
RESPONSE=$(curl -s -X GET "$BASE_URL/health/fatigue/$USER_ID")

if echo "$RESPONSE" | grep -q "user_id"; then
    echo -e "${GREEN}✅ 피로도 조회 성공${NC}"
    echo "$RESPONSE" | jq .
else
    echo -e "${RED}❌ 피로도 조회 실패${NC}"
    echo "$RESPONSE"
fi

echo ""
echo "========================================="
echo "2. 날씨 API 테스트"
echo "========================================="

# 현재 날씨 조회
echo -e "${YELLOW}GET /weather/current${NC}"
RESPONSE=$(curl -s -X GET "$BASE_URL/weather/current?latitude=37.5665&longitude=126.9780&sido=서울")

if echo "$RESPONSE" | grep -q "fetched_at"; then
    echo -e "${GREEN}✅ 날씨 조회 성공${NC}"
    echo "$RESPONSE" | jq .
else
    echo -e "${RED}❌ 날씨 조회 실패 (API 키 필요)${NC}"
    echo "$RESPONSE"
fi

echo ""
echo "========================================="
echo "3. 종합 테스트 결과"
echo "========================================="

# 추가 HRV 데이터 입력 (여러 피로도 레벨)
echo -e "${YELLOW}추가 HRV 데이터 입력...${NC}"

for hrv in 50.0 28.0 17.0 10.0; do
    curl -s -X POST "$BASE_URL/health/hrv" \
      -H "Content-Type: application/json" \
      -d '{
        "user_id": "'$USER_ID'",
        "hrv_value": '$hrv',
        "measured_at": "2025-11-26T14:00:00Z"
      }' > /dev/null
    echo "  - HRV: ${hrv}ms 입력 완료"
done

echo ""

# 최종 피로도 확인
echo -e "${YELLOW}최종 피로도 상태:${NC}"
curl -s -X GET "$BASE_URL/health/fatigue/$USER_ID" | jq '{
  current_fatigue_level,
  fatigue_label,
  latest_hrv_value,
  average_fatigue_7days
}'

echo ""
echo "========================================="
echo "✅ 테스트 완료!"
echo "========================================="
echo ""
echo "Swagger UI: http://localhost:11325/docs"
echo ""
