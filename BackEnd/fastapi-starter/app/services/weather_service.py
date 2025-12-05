"""
날씨 서비스
기상청 초단기실황 API + 미세먼지 API 통합
"""
import logging
import os
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import httpx
from sqlalchemy.orm import Session

from app.models.weather import WeatherCache

logger = logging.getLogger(__name__)


class WeatherService:
    """날씨 데이터 조회 및 캐싱 서비스"""

    def __init__(self):
        self.weather_api_key = os.getenv("WEATHER_API_KEY", "")
        self.air_quality_api_key = os.getenv("AIR_QUALITY_API_KEY", "")

        # 기상청 API 엔드포인트
        self.weather_base_url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"

        # 미세먼지 API 엔드포인트
        self.air_quality_base_url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"

    @staticmethod
    def _generate_location_key(latitude: float, longitude: float) -> str:
        """위도경도로부터 캐시 키 생성"""
        return f"{latitude:.4f}_{longitude:.4f}"

    @staticmethod
    def _convert_to_grid(latitude: float, longitude: float) -> tuple[int, int]:
        """
        위도경도를 기상청 격자 좌표로 변환

        간단한 근사 변환 (실제로는 더 정확한 변환 필요)
        """
        # 기준점 (서울 시청 기준)
        RE = 6371.00877  # 지구 반경(km)
        GRID = 5.0       # 격자 간격(km)
        SLAT1 = 30.0     # 투영 위도1(degree)
        SLAT2 = 60.0     # 투영 위도2(degree)
        OLON = 126.0     # 기준점 경도(degree)
        OLAT = 38.0      # 기준점 위도(degree)
        XO = 43          # 기준점 X좌표(GRID)
        YO = 136         # 기준점 Y좌표(GRID)

        # 간단한 변환 (실제로는 Lambert Conformal Conic 투영 사용)
        # 여기서는 근사치만 계산
        nx = int(XO + (longitude - OLON) * GRID * 10)
        ny = int(YO + (latitude - OLAT) * GRID * 10)

        return nx, ny

    async def fetch_weather_data(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict]:
        """
        기상청 초단기실황 API 호출

        Returns:
            {
                "temperature": 25.3,
                "humidity": 65.0,
                "precipitation": 0.0,
                "wind_speed": 2.5
            }
        """
        try:
            # 좌표 검증: 한국 영역만 허용
            # 대한민국 범위: 위도 33~39, 경도 124~132
            if not (33 <= latitude <= 39 and 124 <= longitude <= 132):
                logger.warning(f"⚠️ Coordinates outside Korea: lat={latitude}, lon={longitude}")
                return None

            # 격자 좌표 변환
            nx, ny = self._convert_to_grid(latitude, longitude)

            # 현재 시각 기준 (KST)
            from datetime import timezone, timedelta as td
            kst = timezone(td(hours=9))
            now_kst = datetime.now(kst)

            # 기상청 초단기실황은 매시 정각 기준, 10분 후 발표
            # 현재 시각이 정각+10분 이전이면 2시간 전, 아니면 1시간 전 데이터 사용
            if now_kst.minute < 10:
                # 아직 이번 시간 데이터가 발표 안됨
                base_datetime = now_kst - timedelta(hours=2)
            else:
                base_datetime = now_kst - timedelta(hours=1)

            base_date = base_datetime.strftime("%Y%m%d")
            base_time = base_datetime.strftime("%H00")  # 정각으로 맞춤

            logger.info(f"🕐 Weather API request: {base_date} {base_time} (KST: {now_kst.strftime('%Y-%m-%d %H:%M')})")

            params = {
                "serviceKey": self.weather_api_key,
                "pageNo": 1,
                "numOfRows": 10,
                "dataType": "JSON",
                "base_date": base_date,
                "base_time": base_time,
                "nx": nx,
                "ny": ny
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.weather_base_url, params=params)
                response.raise_for_status()
                data = response.json()

            # 응답 파싱
            if data.get("response", {}).get("header", {}).get("resultCode") != "00":
                logger.error(f"❌ Weather API error: {data}")
                return None

            items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

            weather_data = {}
            for item in items:
                category = item.get("category")
                value = float(item.get("obsrValue", 0))

                if category == "T1H":  # 기온
                    weather_data["temperature"] = value
                elif category == "REH":  # 습도
                    weather_data["humidity"] = value
                elif category == "RN1":  # 1시간 강수량
                    weather_data["precipitation"] = value
                elif category == "WSD":  # 풍속
                    weather_data["wind_speed"] = value

            logger.info(f"✅ Weather data fetched: {weather_data}")
            return weather_data

        except Exception as e:
            logger.error(f"❌ Weather API error: {str(e)}")
            return None

    async def fetch_air_quality_data(
        self,
        sido_name: str = "서울"
    ) -> Optional[Dict]:
        """
        미세먼지 API 호출

        Args:
            sido_name: 시도 이름 (서울, 부산, 대구 등)

        Returns:
            {
                "pm10": 45.0,
                "pm2_5": 25.0
            }
        """
        try:
            params = {
                "serviceKey": self.air_quality_api_key,
                "returnType": "json",
                "numOfRows": 1,
                "pageNo": 1,
                "sidoName": sido_name,
                "ver": "1.0"
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.air_quality_base_url, params=params)
                response.raise_for_status()
                data = response.json()

            # 응답 파싱
            items = data.get("response", {}).get("body", {}).get("items", [])

            if not items:
                logger.error(f"❌ Air quality API: No data")
                return None

            item = items[0]

            # pm10Value, pm25Value는 문자열로 반환됨 ("-" 또는 숫자)
            pm10_raw = item.get("pm10Value", "-")
            pm25_raw = item.get("pm25Value", "-")

            air_quality_data = {
                "pm10": float(pm10_raw) if pm10_raw and pm10_raw != "-" else None,
                "pm2_5": float(pm25_raw) if pm25_raw and pm25_raw != "-" else None
            }

            logger.info(f"✅ Air quality data fetched: {air_quality_data}")
            return air_quality_data

        except Exception as e:
            logger.error(f"❌ Air quality API error: {str(e)}")
            return None

    async def get_combined_weather(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        sido_name: str = "서울"
    ) -> Dict:
        """
        날씨 + 미세먼지 통합 조회 (캐싱 포함)

        캐시 유효 시간: 10분

        Returns:
            {
                "temperature": 25.3,
                "humidity": 65.0,
                "precipitation": 0.0,
                "wind_speed": 2.5,
                "pm10": 45.0,
                "pm2_5": 25.0,
                "cached": True/False
            }
        """
        location_key = self._generate_location_key(latitude, longitude)

        # 캐시 조회
        cached = db.query(WeatherCache)\
            .filter(
                WeatherCache.location_key == location_key,
                WeatherCache.expires_at > datetime.now(timezone.utc)
            )\
            .first()

        if cached:
            logger.info(f"✅ Weather cache hit: {location_key}")
            return {
                "temperature": cached.temperature,
                "humidity": cached.humidity,
                "precipitation": cached.precipitation,
                "wind_speed": cached.wind_speed,
                "pm10": cached.pm10,
                "pm2_5": cached.pm2_5,
                "cached": True,
                "fetched_at": cached.fetched_at
            }

        # 캐시 미스 - API 호출
        logger.info(f"⏳ Weather cache miss, fetching: {location_key}")

        weather_data = await self.fetch_weather_data(latitude, longitude)
        air_quality_data = await self.fetch_air_quality_data(sido_name)

        # API 실패 시 더미 데이터 사용 (개발/테스트용)
        if not weather_data:
            logger.warning(f"⚠️ Weather API failed, using dummy data")
            weather_data = {
                "temperature": 0,
                "humidity": 55.0,
                "precipitation": 0.0,
                "wind_speed": 2.5
            }

        # 병합
        combined = {
            "temperature": weather_data.get("temperature") if weather_data else None,
            "humidity": weather_data.get("humidity") if weather_data else None,
            "precipitation": weather_data.get("precipitation") if weather_data else None,
            "wind_speed": weather_data.get("wind_speed") if weather_data else None,
            "pm10": air_quality_data.get("pm10") if air_quality_data else None,
            "pm2_5": air_quality_data.get("pm2_5") if air_quality_data else None,
            "cached": False,
            "fetched_at": datetime.now(timezone.utc)
        }

        # 캐시 저장 (10분 유효)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        # 기존 캐시 삭제 후 새로 저장
        db.query(WeatherCache).filter(WeatherCache.location_key == location_key).delete()

        cache_entry = WeatherCache(
            location_key=location_key,
            temperature=combined["temperature"],
            humidity=combined["humidity"],
            precipitation=combined["precipitation"],
            wind_speed=combined["wind_speed"],
            pm10=combined["pm10"],
            pm2_5=combined["pm2_5"],
            expires_at=expires_at
        )

        db.add(cache_entry)
        db.commit()

        logger.info(f"✅ Weather cached: {location_key}")
        return combined


# 싱글톤 인스턴스
weather_service = WeatherService()
