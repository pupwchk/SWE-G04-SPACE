import requests
import pandas as pd

# --------------------------------------------------------------------
# 1. 설정: 본인의 Client ID와 파라미터를 입력합니다.
# --------------------------------------------------------------------

# ❗️ 여기에 발급받은 Client ID를 입력하세요
CLIENT_ID = '603838b8-866b-4a5e-99b9-36a2d309602f' 

# 오슬로의 주요 관측소 (Oslo - Blindern)
STATION_ID = 'SN18700'

# 요청 기간 (2019-11-01 ~ 2020-03-30)
# API는 종료 날짜를 포함하지 않으므로, 3월 31일로 설정해야 30일 데이터까지 포함됩니다.
REFERENCE_TIME = '2019-11-01/2020-03-31'

# 요청할 기상 요소 (일(P1D) 단위로 집계)
# (기온, 습도, 기압, 구름 양은 일 평균 / 일조량, 강수량은 일 합계)
ELEMENTS = [
    'mean(air_temperature P1D)',           # 기온 (일 평균)
    'sum(duration_of_sunshine P1D)',     # 일조량 (일 합계)
    'mean(relative_humidity P1D)',         # 습도 (일 평균)
    'mean(air_pressure_at_sea_level P1D)', # 대기압 (일 평균, 해수면 기준)
    'sum(precipitation_amount P1D)',     # 강수량 (일 합계)
    'mean(cloud_area_fraction P1D)',     # 구름 양 (일 평균)
]

# --------------------------------------------------------------------
# 2. Frost API에 데이터 요청
# --------------------------------------------------------------------

# API 엔드포인트
endpoint = 'https://frost.met.no/observations/v0.jsonld'

# 요청 파라미터 설정
parameters = {
    'sources': STATION_ID,
    'referencetime': REFERENCE_TIME,
    'elements': ','.join(ELEMENTS), # 쉼표로 구분된 문자열로 전달
}

print("Frost API에서 데이터 가져오는 중...")

# GET 요청 보내기 (Client ID는 auth 파라미터로 전달)
response = requests.get(
    endpoint,
    params=parameters,
    auth=(CLIENT_ID, '') # 사용자 이름은 Client ID, 비밀번호는 비워둠
)

# --------------------------------------------------------------------
# 3. 응답 처리 및 Pandas DataFrame으로 변환
# --------------------------------------------------------------------

if response.status_code == 200:
    print("데이터 수신 성공!")
    
    # JSON 데이터 로드
    json_data = response.json()
    data = json_data.get('data', [])

    if not data:
        print("경고: 해당 기간 및 관측소에 데이터가 없습니다.")
    else:
        # --------------------------------------------------------------------
        # 4. 보기 쉬운 'Wide' 포맷으로 데이터 재구성 (Pivoting) - (수정됨)
        # --------------------------------------------------------------------
        
        processed_data = []
        for item in data:
            ref_time = item['referenceTime']
            observations = item.get('observations', [])
            
            row = {'time': ref_time}
            for obs in observations:
                element_id = obs['elementId'] # 예: 'mean(air_temperature P1D)'
                value = obs.get('value')
                
                # ❗️ [수정됨] 'mean'이 아닌 'air_temperature'를 추출합니다.
                try:
                    # 'mean(air_temperature P1D)' -> 'air_temperature P1D)'
                    split_1 = element_id.split('(')[1]
                    # 'air_temperature P1D)' -> 'air_temperature'
                    simple_element_name = split_1.split(' ')[0]
                except IndexError:
                    # 예외 처리 (예: 'air_temperature' 처럼 괄호가 없는 경우)
                    simple_element_name = element_id

                row[simple_element_name] = value
                
            processed_data.append(row)

        # 리스트를 DataFrame으로 변환
        df = pd.DataFrame(processed_data)
        
        # 'time' 컬럼을 datetime 객체로 변환하고 인덱스로 설정
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time']).dt.tz_localize(None)
            df = df.set_index('time')
        else:
            print("오류: 'time' 컬럼을 찾을 수 없습니다.")
            exit() # 'time'이 없으면 진행 불가능하므로 종료

        # 컬럼 순서 정리 (요청한 순서와 비슷하게)
        column_order = [
            'air_temperature', 
            'duration_of_sunshine', 
            'relative_humidity', 
            'air_pressure_at_sea_level',
            'precipitation_amount',
            'cloud_area_fraction'
        ]
        
        # 실제 존재하는 컬럼들만 필터링
        final_columns = [col for col in column_order if col in df.columns]
        
        # ❗️ [추가] 누락된 컬럼이 있는지 확인
        missing_cols = set(column_order) - set(final_columns)
        if missing_cols:
            print(f"\n참고: 다음 요소는 데이터가 없거나 API에서 반환되지 않았습니다: {missing_cols}")
            
        df_final = df[final_columns]

        # # 리스트를 DataFrame으로 변환
        # df = pd.DataFrame(processed_data)

        # # ----------------------------------------------------
        # # ❗️ [추가] 디버깅 코드: df의 실제 컬럼과 데이터를 확인합니다.
        # # ----------------------------------------------------
        # print("\n--- [디버깅] 필터링 전 df 컬럼 목록 ---")
        # print(df.columns)

        # print("\n--- [디버깅] 필터링 전 df 상위 5개 행 ---")
        # print(df.head())
        # # ----------------------------------------------------

        # # 'time' 컬럼을 datetime 객체로 변환하고 인덱스로 설정
        # if 'time' in df.columns: # time 컬럼이 있을 때만 실행
        #     df['time'] = pd.to_datetime(df['time']).dt.tz_localize(None)
        #     df = df.set_index('time')
        # else:
        #     print("경고: 'time' 컬럼이 원본 데이터에 없습니다.")

        # # 'time' 컬럼을 datetime 객체로 변환하고 인덱스로 설정
        # df['time'] = pd.to_datetime(df['time']).dt.tz_localize(None)
        # df = df.set_index('time')
        
        # # 컬럼 순서 정리 (요청한 순서와 비슷하게)
        # column_order = [
        #     'air_temperature', 
        #     'duration_of_sunshine', 
        #     'relative_humidity', 
        #     'air_pressure_at_sea_level',
        #     'precipitation_amount',
        #     'cloud_area_fraction'
        # ]
        # # 데이터가 없는 컬럼이 있을 수 있으므로, 실제 존재하는 컬럼만 필터링
        # final_columns = [col for col in column_order if col in df.columns]
        # df_final = df[final_columns]

        # 리스트를 DataFrame으로 변환
        df = pd.DataFrame(processed_data)

        # -----------------------------------------------------------------
        # ❗️ [수정] 'time' 컬럼 변환 및 인덱스 설정 (순서가 중요합니다)
        # -----------------------------------------------------------------
        
        # 1. 'time' 컬럼이 있는지 확인부터 합니다.
        if 'time' in df.columns:
            # 2. 'time' 컬럼의 타입을 datetime으로 *먼저* 변환합니다.
            # (이 시점에는 'time'이 컬럼이어야 합니다.)
            df['time'] = pd.to_datetime(df['time']).dt.tz_localize(None)
            
            # 3. 변환이 끝난 후, 'time'을 인덱스로 설정합니다.
            # (이 코드가 실행되면 'time'은 컬럼에서 사라집니다.)
            df = df.set_index('time')
        else:
            print("오류: 'time' 컬럼을 찾을 수 없습니다. (파싱 로직 확인 필요)")
            exit() # 'time'이 없으면 진행 불가능

        # 컬럼 순서 정리 (요청한 순서와 비슷하게)
        column_order = [
            'air_temperature', 
            'duration_of_sunshine', 
            'relative_humidity', 
            'air_pressure_at_sea_level',
            'precipitation_amount',
            'cloud_area_fraction'
        ]
        
        # 실제 존재하는 컬럼들만 필터링
        # (이제 'time'이 인덱스이므로, df.columns에는 기상 요소만 있습니다)
        final_columns = [col for col in column_order if col in df.columns]
        
        # (옵션) 누락된 컬럼이 있는지 확인
        missing_cols = set(column_order) - set(df.columns)
        if missing_cols:
            print(f"\n참고: 다음 요소는 데이터가 없거나 API에서 반환되지 않았습니다: {missing_cols}")
            
        df_final = df[final_columns]

        print("\n--- 데이터 (Pandas DataFrame) ---")
        print(df_final.head()) # .head()를 붙여 상위 5개만 출력

        # print("\n--- 데이터 (Pandas DataFrame) ---")
        # print(df_final)

        # (옵션) CSV 파일로 저장
        df_final.to_csv("./Model/fatigue/output/oslo_weather_2019_2020.csv")
        print("\n'oslo_weather_2019_2020.csv' 파일로 저장되었습니다.")

elif response.status_code == 401:
    print("오류: 인증 실패 (401).")
    print("Client ID가 정확한지, 혹은 유효한지 확인하세요.")
elif response.status_code == 403:
    print("오류: 접근 거부 (403).")
    print("Client ID가 비활성화되었거나 요청 권한이 없을 수 있습니다.")
elif response.status_code == 404:
    print("오류: 찾을 수 없음 (404).")
    print(f"관측소 ID ({STATION_ID}) 또는 API 엔드포인트가 잘못되었을 수 있습니다.")
else:
    print(f"오류 발생: Status Code {response.status_code}")
    print("응답 내용:", response.text)