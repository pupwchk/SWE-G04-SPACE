#!/usr/bin/env python3
"""
시나리오 2 통합 테스트
사용자 주도형 대화 및 가전 제어 플로우 검증
"""
import asyncio
import sys
import json
from typing import Dict, Any

import requests
from colorama import init, Fore, Style

init(autoreset=True)

# API 기본 URL
BASE_URL = "http://localhost:11325/api"

# 테스트 사용자 ID
TEST_USER_ID = "test_user_scenario2"


def print_step(step: str):
    """테스트 단계 출력"""
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.CYAN}{step}")
    print(f"{Fore.CYAN}{'=' * 60}\n")


def print_success(message: str):
    """성공 메시지 출력"""
    print(f"{Fore.GREEN}✅ {message}")


def print_error(message: str):
    """에러 메시지 출력"""
    print(f"{Fore.RED}❌ {message}")


def print_info(message: str):
    """정보 메시지 출력"""
    print(f"{Fore.YELLOW}ℹ️  {message}")


def print_json(data: Dict[str, Any]):
    """JSON 데이터 출력"""
    print(f"{Fore.WHITE}{json.dumps(data, indent=2, ensure_ascii=False)}")


def test_chat_environment_complaint():
    """
    테스트 1: 환경 불편 표현 → AI 제안
    """
    print_step("테스트 1: 환경 불편 표현 → AI 제안")

    # 사용자 메시지: "집이 너무 덥다"
    payload = {
        "message": "집이 너무 덥다",
        "context": {}
    }

    print_info(f"Request: POST {BASE_URL}/chat/{TEST_USER_ID}/message")
    print_json(payload)

    try:
        response = requests.post(
            f"{BASE_URL}/chat/{TEST_USER_ID}/message",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        print_success("응답 받음")
        print_json(data)

        # 검증
        assert data["intent_type"] in ["environment_complaint", "appliance_request"], \
            f"Unexpected intent_type: {data['intent_type']}"

        if data["needs_control"]:
            assert data["suggestions"] is not None, "suggestions should not be None"
            print_success(f"✅ 제안 생성됨: {len(data['suggestions'])}개 가전")
            return data["suggestions"], data["session_id"]
        else:
            print_info("제어가 필요하지 않음")
            return None, data.get("session_id")

    except requests.exceptions.RequestException as e:
        print_error(f"API 호출 실패: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"Response: {e.response.text}")
        return None, None
    except AssertionError as e:
        print_error(f"검증 실패: {str(e)}")
        return None, None
    except Exception as e:
        print_error(f"예상치 못한 에러: {str(e)}")
        return None, None


def test_chat_approval(suggestions: list, session_id: str, user_response: str = "좋아"):
    """
    테스트 2: 사용자 승인 → 가전 제어 실행
    """
    print_step(f"테스트 2: 사용자 승인 → 가전 제어 실행 ('{user_response}')")

    if not suggestions:
        print_error("제안이 없어서 테스트 스킵")
        return False

    payload = {
        "user_response": user_response,
        "original_plan": {"recommendations": suggestions},
        "session_id": session_id
    }

    print_info(f"Request: POST {BASE_URL}/chat/{TEST_USER_ID}/approve")
    print_json(payload)

    try:
        response = requests.post(
            f"{BASE_URL}/chat/{TEST_USER_ID}/approve",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        print_success("응답 받음")
        print_json(data)

        # 검증
        if user_response in ["좋아", "응", "그래", "okay", "ok"]:
            assert data["approved"] is True, "Should be approved"
            print_success(f"✅ 승인됨 (수정: {data.get('has_modification', False)})")

            if data.get("execution_results"):
                success_count = sum(1 for r in data["execution_results"] if r["status"] == "success")
                total_count = len(data["execution_results"])
                print_success(f"✅ 실행 결과: {success_count}/{total_count} 성공")

        elif user_response in ["아니야", "괜찮아", "싫어"]:
            assert data["approved"] is False, "Should be rejected"
            print_success("✅ 거절됨")
        else:
            # 수정 사항 포함
            print_info(f"수정 여부: {data.get('has_modification', False)}")
            if data.get("has_modification"):
                print_info(f"수정 내용: {data.get('modifications')}")

        return True

    except requests.exceptions.RequestException as e:
        print_error(f"API 호출 실패: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"Response: {e.response.text}")
        return False
    except AssertionError as e:
        print_error(f"검증 실패: {str(e)}")
        return False
    except Exception as e:
        print_error(f"예상치 못한 에러: {str(e)}")
        return False


def test_chat_modification(suggestions: list, session_id: str):
    """
    테스트 3: 사용자 수정 후 승인
    """
    print_step("테스트 3: 사용자 수정 후 승인")

    if not suggestions:
        print_error("제안이 없어서 테스트 스킵")
        return False

    # "에어컨은 24도로 해줘"
    return test_chat_approval(suggestions, session_id, "에어컨은 24도로 해줘")


def test_chat_rejection(suggestions: list, session_id: str):
    """
    테스트 4: 사용자 거절
    """
    print_step("테스트 4: 사용자 거절")

    if not suggestions:
        print_error("제안이 없어서 테스트 스킵")
        return False

    return test_chat_approval(suggestions, session_id, "아니야 괜찮아")


def test_chat_history():
    """
    테스트 5: 채팅 히스토리 조회
    """
    print_step("테스트 5: 채팅 히스토리 조회")

    print_info(f"Request: GET {BASE_URL}/chat/{TEST_USER_ID}/history")

    try:
        response = requests.get(
            f"{BASE_URL}/chat/{TEST_USER_ID}/history",
            params={"limit": 10},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        print_success("응답 받음")
        print_json(data)

        # 검증
        assert "conversation_history" in data, "conversation_history missing"
        print_success(f"✅ 히스토리: {len(data['conversation_history'])}개 메시지")

        return True

    except requests.exceptions.RequestException as e:
        print_error(f"API 호출 실패: {str(e)}")
        return False
    except AssertionError as e:
        print_error(f"검증 실패: {str(e)}")
        return False
    except Exception as e:
        print_error(f"예상치 못한 에러: {str(e)}")
        return False


def test_general_chat():
    """
    테스트 6: 일반 대화
    """
    print_step("테스트 6: 일반 대화 (가전 제어 불필요)")

    payload = {
        "message": "안녕? 오늘 날씨 어때?",
        "context": {}
    }

    print_info(f"Request: POST {BASE_URL}/chat/{TEST_USER_ID}/message")
    print_json(payload)

    try:
        response = requests.post(
            f"{BASE_URL}/chat/{TEST_USER_ID}/message",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        print_success("응답 받음")
        print_json(data)

        # 검증
        assert data["intent_type"] == "general_chat" or data["needs_control"] is False, \
            f"Should be general chat"
        print_success("✅ 일반 대화로 처리됨")

        return True

    except requests.exceptions.RequestException as e:
        print_error(f"API 호출 실패: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"Response: {e.response.text}")
        return False
    except AssertionError as e:
        print_error(f"검증 실패: {str(e)}")
        return False
    except Exception as e:
        print_error(f"예상치 못한 에러: {str(e)}")
        return False


def test_clear_session():
    """
    테스트 7: 세션 초기화
    """
    print_step("테스트 7: 세션 초기화")

    print_info(f"Request: DELETE {BASE_URL}/chat/{TEST_USER_ID}/session")

    try:
        response = requests.delete(
            f"{BASE_URL}/chat/{TEST_USER_ID}/session",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        print_success("응답 받음")
        print_json(data)

        assert data["status"] == "ok", "Status should be ok"
        print_success("✅ 세션 초기화 성공")

        return True

    except requests.exceptions.RequestException as e:
        print_error(f"API 호출 실패: {str(e)}")
        return False
    except AssertionError as e:
        print_error(f"검증 실패: {str(e)}")
        return False
    except Exception as e:
        print_error(f"예상치 못한 에러: {str(e)}")
        return False


def main():
    """메인 테스트 실행"""
    print(f"{Fore.MAGENTA}{Style.BRIGHT}")
    print("=" * 60)
    print("시나리오 2 통합 테스트")
    print("=" * 60)
    print(f"{Style.RESET_ALL}")

    print_info(f"API Base URL: {BASE_URL}")
    print_info(f"Test User ID: {TEST_USER_ID}")

    # 서버 연결 확인
    print_step("서버 연결 확인")
    try:
        response = requests.get(f"http://localhost:11325/docs", timeout=5)
        print_success("FastAPI 서버 연결 성공")
    except requests.exceptions.RequestException:
        print_error("FastAPI 서버에 연결할 수 없습니다.")
        print_info("서버를 시작하세요: poetry run uvicorn app.main:app --reload --port 11325")
        sys.exit(1)

    results = {
        "환경 불편 표현": False,
        "승인 후 실행": False,
        "수정 후 승인": False,
        "거절": False,
        "히스토리 조회": False,
        "일반 대화": False,
        "세션 초기화": False
    }

    # 테스트 1: 환경 불편 표현
    suggestions, session_id = test_chat_environment_complaint()
    results["환경 불편 표현"] = suggestions is not None or session_id is not None

    if suggestions:
        # 테스트 2: 승인 후 실행
        results["승인 후 실행"] = test_chat_approval(suggestions, session_id, "좋아")

        # 테스트 3: 수정 후 승인
        # 새로운 제안 생성
        suggestions2, session_id2 = test_chat_environment_complaint()
        if suggestions2:
            results["수정 후 승인"] = test_chat_modification(suggestions2, session_id2)

        # 테스트 4: 거절
        suggestions3, session_id3 = test_chat_environment_complaint()
        if suggestions3:
            results["거절"] = test_chat_rejection(suggestions3, session_id3)

    # 테스트 5: 히스토리 조회
    results["히스토리 조회"] = test_chat_history()

    # 테스트 6: 일반 대화
    results["일반 대화"] = test_general_chat()

    # 테스트 7: 세션 초기화
    results["세션 초기화"] = test_clear_session()

    # 결과 요약
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}")
    print("=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    print(f"{Style.RESET_ALL}")

    for test_name, result in results.items():
        status = f"{Fore.GREEN}✅ PASS" if result else f"{Fore.RED}❌ FAIL"
        print(f"{status} - {test_name}")

    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    pass_rate = (passed_tests / total_tests) * 100

    print(f"\n{Fore.CYAN}총 {total_tests}개 테스트 중 {passed_tests}개 통과 ({pass_rate:.1f}%)")

    if passed_tests == total_tests:
        print(f"{Fore.GREEN}{Style.BRIGHT}🎉 모든 테스트 통과!")
        sys.exit(0)
    else:
        print(f"{Fore.YELLOW}⚠️  일부 테스트 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
