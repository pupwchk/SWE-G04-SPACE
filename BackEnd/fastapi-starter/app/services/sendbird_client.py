"""
Sendbird API 클라이언트
"""
import httpx
import logging
from typing import Optional, Dict, Any
from app.config.sendbird import SendbirdConfig

logger = logging.getLogger(__name__)


class SendbirdChatClient:
    """Sendbird Chat API 클라이언트"""
    
    def __init__(self):
        self.base_url = SendbirdConfig.CHAT_API_BASE
        self.headers = SendbirdConfig.get_chat_headers()
    
    async def send_message(
        self,
        channel_url: str,
        message: str,
        sender_id: Optional[str] = None,
        user_id: Optional[str] = None,
        data: Optional[str] = None,
        custom_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        채널에 메시지 전송 (채널이 없으면 자동 생성)

        Args:
            channel_url: 채널 URL
            message: 메시지 내용
            sender_id: 발신자 ID (기본값: AI assistant)
            user_id: 채널에 추가할 사용자 ID (채널 생성 시 필요)
            data: 메시지 메타데이터 (JSON 문자열)
            custom_type: 메시지 커스텀 타입 (예: "appliance_suggestion")

        Returns:
            API 응답
        """
        if sender_id is None:
            sender_id = SendbirdConfig.AI_USER_ID

        url = f"{self.base_url}/group_channels/{channel_url}/messages"

        payload = {
            "message_type": "MESG",
            "user_id": sender_id,
            "message": message
        }

        # 메타데이터 추가
        if data:
            payload["data"] = data
        if custom_type:
            payload["custom_type"] = custom_type

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()

                logger.info(f"✅ Message sent to channel {channel_url}")
                return response.json()

        except httpx.HTTPStatusError as e:
            # 채널이 없으면 자동 생성 후 재시도
            if e.response.status_code == 400 and "Channel\" not found" in e.response.text:
                logger.warning(f"⚠️  Channel {channel_url} not found, creating...")

                if user_id:
                    # 채널 생성
                    await self.create_channel(
                        channel_url=channel_url,
                        user_ids=[user_id, SendbirdConfig.AI_USER_ID]
                    )

                    # 메시지 재전송
                    async with httpx.AsyncClient() as retry_client:
                        retry_response = await retry_client.post(
                            url,
                            headers=self.headers,
                            json=payload,
                            timeout=10.0
                        )
                        retry_response.raise_for_status()
                        logger.info(f"✅ Message sent to new channel {channel_url}")
                        return retry_response.json()
                else:
                    logger.error(f"❌ Cannot create channel: user_id not provided")
                    raise
            else:
                logger.error(f"❌ Failed to send message: {e.response.status_code} - {e.response.text}")
                raise
        except Exception as e:
            logger.error(f"❌ Error sending message: {str(e)}")
            raise
    
    async def get_channel(self, channel_url: str) -> Optional[Dict[str, Any]]:
        """채널 정보 조회"""
        url = f"{self.base_url}/group_channels/{channel_url}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        except Exception as e:
            logger.error(f"❌ Error getting channel: {str(e)}")
            raise
    
    async def create_channel(
        self,
        channel_url: Optional[str],
        user_ids: list[str],
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        채널 생성 또는 기존 채널 조회

        is_distinct=True이면 같은 멤버 조합의 채널이 이미 있으면 그 채널을 반환
        """
        url = f"{self.base_url}/group_channels"

        payload = {
            "user_ids": user_ids,
            "is_distinct": True,
            "name": name or f"Chat with {SendbirdConfig.AI_USER_NAME}"
        }

        # channel_url이 지정되면 사용
        if channel_url:
            payload["channel_url"] = channel_url

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()

                channel_data = response.json()
                created_channel_url = channel_data.get("channel_url")
                logger.info(f"✅ Channel ready: {created_channel_url}")
                return channel_data

        except Exception as e:
            logger.error(f"❌ Error creating channel: {str(e)}")
            raise


class SendbirdCallsClient:
    """Sendbird Calls API 클라이언트"""

    def __init__(self):
        self.base_url = SendbirdConfig.CALLS_API_BASE
        self.headers = SendbirdConfig.get_calls_headers()

    async def register_ai_assistant(
        self,
        assistant_id: str = None
    ) -> Dict[str, Any]:
        """
        AI assistant를 SendBird Chat & Calls에 자동 등록

        2단계 프로세스:
        1. Chat Platform API로 사용자 생성 및 access_token 발급
        2. Calls API로 인증 (/v1/authenticate)

        Args:
            assistant_id: AI assistant의 사용자 ID (기본값: SendbirdConfig.AI_USER_ID)

        Returns:
            등록 결과 딕셔너리
        """
        if assistant_id is None:
            assistant_id = SendbirdConfig.AI_USER_ID

        # Step 1: Chat API를 사용하여 사용자 생성 및 access_token 발급
        chat_base_url = f"https://api-{SendbirdConfig.APP_ID}.sendbird.com/v3"
        chat_user_url = f"{chat_base_url}/users"

        chat_payload = {
            "user_id": assistant_id,
            "nickname": SendbirdConfig.AI_USER_NAME,
            "profile_url": SendbirdConfig.AI_PROFILE_URL,
            "issue_access_token": True
        }

        access_token = None
        user_already_exists = False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    chat_user_url,
                    headers=SendbirdConfig.get_chat_headers(),
                    json=chat_payload,
                    timeout=10.0
                )
                response.raise_for_status()

                chat_result = response.json()
                access_token = chat_result.get("access_token")
                logger.info(f"✅ AI assistant '{assistant_id}' created in Chat Platform")

        except httpx.HTTPStatusError as e:
            # 400 에러 + unique constraint 위반 = 이미 존재하는 사용자
            if e.response.status_code == 400:
                error_text = e.response.text.lower()
                if "unique constraint" in error_text or "already exists" in error_text:
                    logger.info(f"ℹ️ AI assistant '{assistant_id}' already exists in Chat Platform")
                    user_already_exists = True

                    # 기존 사용자의 access_token 조회
                    try:
                        async with httpx.AsyncClient() as client:
                            user_response = await client.get(
                                f"{chat_user_url}/{assistant_id}",
                                headers=SendbirdConfig.get_chat_headers(),
                                timeout=10.0
                            )
                            user_response.raise_for_status()
                            user_data = user_response.json()
                            access_token = user_data.get("access_token")

                            # access_token이 없으면 새로 발급
                            if not access_token:
                                logger.info(f"🔑 Issuing new access token for '{assistant_id}'")
                                async with httpx.AsyncClient() as token_client:
                                    token_response = await token_client.post(
                                        f"{chat_user_url}/{assistant_id}/token",
                                        headers=SendbirdConfig.get_chat_headers(),
                                        timeout=10.0
                                    )
                                    token_response.raise_for_status()
                                    token_data = token_response.json()
                                    access_token = token_data.get("token")
                    except Exception as token_error:
                        logger.warning(f"⚠️ Failed to get access token: {token_error}")
                else:
                    logger.error(f"❌ Failed to register AI assistant: {e.response.status_code} - {e.response.text}")
                    raise
            else:
                logger.error(f"❌ Failed to register AI assistant: {e.response.status_code} - {e.response.text}")
                raise
        except Exception as e:
            logger.error(f"❌ Error registering AI assistant in Chat Platform: {str(e)}")
            raise

        # Step 2: Calls API로 인증
        calls_auth_url = f"{self.base_url}/authenticate"
        calls_payload = {
            "user_id": assistant_id
        }

        # access_token이 있으면 추가
        if access_token:
            calls_payload["access_token"] = access_token

        try:
            async with httpx.AsyncClient() as client:
                calls_response = await client.post(
                    calls_auth_url,
                    headers=self.headers,
                    json=calls_payload,
                    timeout=10.0
                )
                calls_response.raise_for_status()

                calls_result = calls_response.json()
                logger.info(f"✅ AI assistant '{assistant_id}' authenticated with SendBird Calls")

                return {
                    "status": "success",
                    "user_id": assistant_id,
                    "chat_registered": True,
                    "calls_authenticated": True,
                    "user_already_exists": user_already_exists,
                    "calls_result": calls_result
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Failed to authenticate with Calls API: {e.response.status_code} - {e.response.text}")
            # Calls 인증 실패해도 Chat 등록은 성공했으므로 부분 성공 반환
            return {
                "status": "partial_success",
                "user_id": assistant_id,
                "chat_registered": True,
                "calls_authenticated": False,
                "error": f"Calls auth failed: {e.response.text}"
            }
        except Exception as e:
            logger.error(f"❌ Error authenticating with Calls API: {str(e)}")
            return {
                "status": "partial_success",
                "user_id": assistant_id,
                "chat_registered": True,
                "calls_authenticated": False,
                "error": str(e)
            }

    async def authenticate_user(
        self,
        user_id: str,
        nickname: Optional[str] = None,
        profile_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        일반 사용자를 SendBird Chat & Calls에 인증
        iOS 앱에서 로그인 후 호출하여 SendBird Calls SDK 초기화용 토큰 발급

        Args:
            user_id: 사용자 ID (이메일 또는 UUID)
            nickname: 사용자 닉네임 (선택)
            profile_url: 프로필 이미지 URL (선택)

        Returns:
            {
                "user_id": str,
                "access_token": str,
                "calls_authenticated": bool
            }
        """
        # Step 1: Chat API를 사용하여 사용자 생성/조회 및 access_token 발급
        chat_base_url = f"https://api-{SendbirdConfig.APP_ID}.sendbird.com/v3"
        chat_user_url = f"{chat_base_url}/users"

        chat_payload = {
            "user_id": user_id,
            "nickname": nickname or user_id,
            "profile_url": profile_url or "",
            "issue_access_token": True
        }

        access_token = None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    chat_user_url,
                    headers=SendbirdConfig.get_chat_headers(),
                    json=chat_payload,
                    timeout=10.0
                )
                response.raise_for_status()

                chat_result = response.json()
                access_token = chat_result.get("access_token")
                logger.info(f"✅ User '{user_id}' created in Chat Platform")

        except httpx.HTTPStatusError as e:
            # 이미 존재하는 사용자인 경우 access_token 조회
            if e.response.status_code == 400:
                error_text = e.response.text.lower()
                if "unique constraint" in error_text or "already exists" in error_text:
                    logger.info(f"ℹ️ User '{user_id}' already exists, fetching access token")

                    try:
                        async with httpx.AsyncClient() as client:
                            user_response = await client.get(
                                f"{chat_user_url}/{user_id}",
                                headers=SendbirdConfig.get_chat_headers(),
                                timeout=10.0
                            )
                            user_response.raise_for_status()
                            user_data = user_response.json()
                            access_token = user_data.get("access_token")

                            # access_token이 없으면 새로 발급
                            if not access_token:
                                logger.info(f"🔑 Issuing new access token for '{user_id}'")
                                async with httpx.AsyncClient() as token_client:
                                    token_response = await token_client.post(
                                        f"{chat_user_url}/{user_id}/token",
                                        headers=SendbirdConfig.get_chat_headers(),
                                        timeout=10.0
                                    )
                                    token_response.raise_for_status()
                                    token_data = token_response.json()
                                    access_token = token_data.get("token")
                    except Exception as token_error:
                        logger.error(f"❌ Failed to get access token: {token_error}")
                        raise
                else:
                    logger.error(f"❌ Failed to create user: {e.response.status_code} - {e.response.text}")
                    raise
            else:
                raise
        except Exception as e:
            logger.error(f"❌ Error creating user in Chat Platform: {str(e)}")
            raise

        if not access_token:
            raise Exception("Failed to obtain access_token from Chat Platform")

        # Step 2: Calls API로 인증
        calls_auth_url = f"{self.base_url}/authenticate"
        calls_payload = {
            "user_id": user_id,
            "access_token": access_token
        }

        try:
            async with httpx.AsyncClient() as client:
                calls_response = await client.post(
                    calls_auth_url,
                    headers=self.headers,
                    json=calls_payload,
                    timeout=10.0
                )
                calls_response.raise_for_status()

                logger.info(f"✅ User '{user_id}' authenticated with SendBird Calls")

                return {
                    "user_id": user_id,
                    "access_token": access_token,
                    "calls_authenticated": True
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Failed to authenticate with Calls API: {e.response.status_code} - {e.response.text}")
            # Calls 인증 실패해도 access_token은 반환
            return {
                "user_id": user_id,
                "access_token": access_token,
                "calls_authenticated": False,
                "error": f"Calls auth failed: {e.response.text}"
            }
        except Exception as e:
            logger.error(f"❌ Error authenticating with Calls API: {str(e)}")
            return {
                "user_id": user_id,
                "access_token": access_token,
                "calls_authenticated": False,
                "error": str(e)
            }

    async def make_call(
        self,
        caller_id: str,
        callee_id: str,
        call_type: str = "voice"
    ) -> Dict[str, Any]:
        """
        전화 발신
        
        Args:
            caller_id: 발신자 ID (보통 AI assistant)
            callee_id: 수신자 ID (사용자)
            call_type: 통화 타입 (voice/video)
        
        Returns:
            API 응답
        """
        url = f"{self.base_url}/calls"
        
        payload = {
            "caller": {
                "user_id": caller_id
            },
            "callee": {
                "user_id": callee_id
            },
            "call_type": call_type
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                
                logger.info(f"✅ Call initiated: {caller_id} -> {callee_id}")
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Failed to make call: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ Error making call: {str(e)}")
            raise
    
    async def end_call(self, call_id: str) -> Dict[str, Any]:
        """통화 종료"""
        url = f"{self.base_url}/calls/{call_id}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    url,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                
                logger.info(f"✅ Call ended: {call_id}")
                return response.json()
                
        except Exception as e:
            logger.error(f"❌ Error ending call: {str(e)}")
            raise


