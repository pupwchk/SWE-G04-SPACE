import requests
import pandas as pd
import numpy as np
from datetime import datetime

class BioWeatherConditionScorer:
    def __init__(self):
        # 가중치 설정 (수면/생체 65%, 환경/활동 35%)
        self.weights = {
            'sleep': 0.35,
            'ans': 0.30,
            'load': 0.15,
            'weather': 0.20
        }
        # Open-Meteo API 엔드포인트
        self.api_url = "https://api.open-meteo.com/v1/forecast"

    def _fetch_open_meteo_data(self, lat, lon):
        """
        Open-Meteo API를 이용해 '어제'와 '오늘'의 날씨 데이터를 한 번에 가져옵니다.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": [
                "temperature_2m_mean",       # 평균 기온
                "relative_humidity_2m_mean", # 평균 습도
                "precipitation_sum",         # 강수량
                "wind_speed_10m_max",        # 최대 풍속 (체감온도용)
                "sunshine_duration",         # 일조 시간 (초 단위)
                "surface_pressure_mean"      # 평균 기압 (기상병 예측용)
            ],
            "past_days": 1,     # 어제 데이터 포함
            "forecast_days": 1, # 오늘 데이터 포함
            "timezone": "Asia/Seoul"
        }

        try:
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            daily = data.get("daily", {})
            
            # Index 0: 어제, Index 1: 오늘
            yesterday = {
                "temp": daily["temperature_2m_mean"][0],
                "humidity": daily["relative_humidity_2m_mean"][0],
                "rain": daily["precipitation_sum"][0],
                "wind": daily["wind_speed_10m_max"][0],
                "sunshine": daily["sunshine_duration"][0] / 3600, # 초->시간 변환
                "pressure": daily["surface_pressure_mean"][0]
            }
            
            today = {
                "temp": daily["temperature_2m_mean"][1],
                "humidity": daily["relative_humidity_2m_mean"][1],
                "rain": daily["precipitation_sum"][1],
                "wind": daily["wind_speed_10m_max"][1],
                "sunshine": daily["sunshine_duration"][1] / 3600,
                "pressure": daily["surface_pressure_mean"][1]
            }
            
            return today, yesterday

        except Exception as e:
            print(f"⚠️ 날씨 데이터 수집 실패: {e}")
            # 실패 시 기본값 반환 (점수에 영향 없는 쾌적한 상태 가정)
            default_w = {"temp": 20, "humidity": 50, "rain": 0, "wind": 0, "sunshine": 10, "pressure": 1013}
            return default_w, default_w

    def _calculate_bio_score(self, health_data, history_mean):
        """생체 데이터 점수 계산 (이전 로직 유지)"""
        # 1. 수면 (7.5시간 기준)
        sleep_min = health_data.get('sleep_minutes', 420)
        s_score = np.interp(sleep_min, [240, 450], [0, 100])

        # 2. 자율신경계 (RHR/HRV - Baseline 대비)
        curr_rhr = health_data.get('resting_heart_rate', 65)
        base_rhr = history_mean.get('resting_heart_rate', 65)
        curr_hrv = health_data.get('hrv_sdnn', 50)
        base_hrv = history_mean.get('hrv_sdnn', 50)

        rhr_diff = max(0, curr_rhr - base_rhr)
        rhr_score = np.interp(rhr_diff, [0, 10], [100, 0]) # 10bpm 오르면 0점
        
        hrv_diff = max(0, base_hrv - curr_hrv)
        hrv_score = np.interp(hrv_diff, [0, 20], [100, 0]) # 20ms 떨어지면 0점
        
        ans_score = (rhr_score + hrv_score) / 2

        # 3. 활동 부하 (어제 활동량)
        yest_steps = health_data.get('yesterday_steps', 5000)
        base_steps = history_mean.get('steps', 5000)
        
        ratio = yest_steps / base_steps if base_steps > 0 else 1.0
        if ratio <= 1.1: l_score = 100
        else: l_score = np.interp(ratio, [1.1, 2.0], [100, 20])

        return s_score, ans_score, l_score

    def _calculate_weather_score(self, curr_w, prev_w):
        """날씨 스트레스 및 변화량(Delta) 계산"""
        penalty = 0
        reasons = []

        # 1. 절대적 요인 (체감온도/불쾌지수)
        t, h, v = curr_w['temp'], curr_w['humidity'], curr_w['wind']
        
        if t >= 20: # 여름형
            di = 0.81 * t + 0.01 * h * (0.99 * t - 14.3) + 46.3
            if di >= 80: penalty += 30; reasons.append("매우 불쾌함(고온다습)")
            elif di >= 75: penalty += 15; reasons.append("불쾌함")
        elif t <= 10: # 겨울형
            wct = 13.12 + 0.6215*t - 11.37*(v**0.16) + 0.3965*t*(v**0.16)
            if wct <= -10: penalty += 30; reasons.append("극한 추위")
            elif wct <= 5: penalty += 15; reasons.append("추움(체감온도 낮음)")

        # 2. 변화 요인 (기상병)
        # 기압 저하
        delta_p = curr_w['pressure'] - prev_w['pressure']
        if delta_p < -5:
            p_pen = np.interp(abs(delta_p), [5, 15], [10, 40])
            penalty += p_pen
            reasons.append(f"저기압 접근({delta_p:.1f}hPa)")
        
        # 기온 급변
        delta_t = abs(curr_w['temp'] - prev_w['temp'])
        if delta_t >= 7:
            penalty += 20
            reasons.append(f"큰 일교차/기온급변({delta_t:.1f}℃)")

        # 3. 기타 요인
        if curr_w['rain'] >= 10: penalty += 15; reasons.append("많은 비/눈")
        if curr_w['sunshine'] < 2: penalty += 10; reasons.append("일조량 부족")

        return max(0, 100 - penalty), reasons

    def get_condition_score(self, health_data, history_mean, lat=37.5665, lon=126.9780):
        """
        [메인 함수]
        - health_data: 오늘의 생체 데이터 (dict)
        - history_mean: 과거 평균 데이터 (dict)
        - lat, lon: 위치 (기본값: 서울 시청)
        """
        # 1. 날씨 자동 수집 (API 호출)
        print(f"📡 Open-Meteo 날씨 데이터 수집 중... (위치: {lat}, {lon})")
        curr_w, prev_w = self._fetch_open_meteo_data(lat, lon)
        
        # 2. 점수 계산
        s_score, ans_score, l_score = self._calculate_bio_score(health_data, history_mean)
        w_score, w_reasons = self._calculate_weather_score(curr_w, prev_w)

        # 3. 최종 점수 합산
        final_score = (
            s_score * self.weights['sleep'] +
            ans_score * self.weights['ans'] +
            l_score * self.weights['load'] +
            w_score * self.weights['weather']
        )

        # 4. 결과 포맷팅
        status = "최상"
        if final_score < 40: status = "휴식 시급"
        elif final_score < 60: status = "피로함"
        elif final_score < 80: status = "보통/양호"

        return {
            "total_score": round(final_score, 1),
            "status": status,
            "breakdown": {
                "sleep": round(s_score, 1),
                "bio_rhythm": round(ans_score, 1),
                "activity_load": round(l_score, 1),
                "environment": round(w_score, 1)
            },
            "weather_context": {
                "today_summary": f"{curr_w['temp']}℃, {curr_w['humidity']}%, {curr_w['rain']}mm",
                "pressure_change": round(curr_w['pressure'] - prev_w['pressure'], 1),
                "temp_change": round(curr_w['temp'] - prev_w['temp'], 1),
                "risk_factors": w_reasons
            }
        }

# ============================================================================
# 🚀 실행 예시
# ============================================================================

# 1. 내 과거 평균 데이터 (HealthKit 등에서 미리 계산된 값)
my_history = {
    "resting_heart_rate": 65,  # 평소 RHR
    "hrv_sdnn": 50,            # 평소 HRV
    "steps": 6000              # 평소 활동량
}

# 2. 오늘 내 생체 데이터 (Apple Watch 등에서 수집)
my_today_health = {
    "sleep_minutes": 390,      # 6.5시간 (약간 부족)
    "resting_heart_rate": 68,  # 평소보다 약간 높음
    "hrv_sdnn": 45,            # 평소보다 약간 낮음
    "yesterday_steps": 5500    # 평소와 비슷
}

# 3. 점수 계산기 실행
scorer = BioWeatherConditionScorer()

# 서울 좌표 (37.5665, 126.9780) 기준 실행
result = scorer.get_condition_score(my_today_health, my_history, lat=37.5665, lon=126.9780)

print("\n" + "="*40)
print(f"🧬 컨디션 점수: {result['total_score']}점 [{result['status']}]")
print("="*40)
print(f"💤 수면 점수: {result['breakdown']['sleep']}")
print(f"❤️ 생체 리듬: {result['breakdown']['bio_rhythm']}")
print(f"🌧️ 환경 점수: {result['breakdown']['environment']}")
print("-" * 40)
print(f"[날씨 분석]")
print(f"• 현재 상태: {result['weather_context']['today_summary']}")
print(f"• 기압 변화: {result['weather_context']['pressure_change']} hPa (음수면 저기압 접근)")
print(f"• 기온 변화: {result['weather_context']['temp_change']} ℃")
if result['weather_context']['risk_factors']:
    print(f"• 감점 요인: {', '.join(result['weather_context']['risk_factors'])}")
else:
    print("• 특이사항 없음 (날씨 쾌적)")