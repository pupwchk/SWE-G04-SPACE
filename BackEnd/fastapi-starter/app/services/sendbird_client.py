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
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        채널에 메시지 전송 (채널이 없으면 자동 생성)

        Args:
            channel_url: 채널 URL
            message: 메시지 내용
            sender_id: 발신자 ID (기본값: AI assistant)
            user_id: 채널에 추가할 사용자 ID (채널 생성 시 필요)

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


