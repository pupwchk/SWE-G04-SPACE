"""
Sendbird Webhook API
채팅 메시지 수신 및 처리
"""
import logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from typing import Dict, Any

from app.services.sendbird_client import SendbirdChatClient, SendbirdCallsClient
from app.services.llm_service import llm_service, memory_service, LLMAction
from app.config.sendbird import SendbirdConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook/sendbird", tags=["Sendbird Webhook"])

# 클라이언트 초기화
chat_client = SendbirdChatClient()
calls_client = SendbirdCallsClient()


@router.post("/chat")
async def sendbird_chat_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Sendbird 채팅 웹훅 수신

    Webhook 설정:
    - Dashboard > Settings > Chat > Webhooks
    - URL: https://your-domain.com/webhook/sendbird/chat
    - Events: message:send
    """
    try:
        logger.info("=" * 80)
        logger.info("🔔 [WEBHOOK-DEBUG] Sendbird webhook received!")

        # JSON 파싱 에러 처리
        try:
            payload = await request.json()
            logger.info(f"📦 [WEBHOOK-DEBUG] Payload: {payload}")
        except Exception as json_error:
            logger.warning(f"⚠️ Invalid JSON in webhook request: {str(json_error)}")
            return {"status": "ignored", "reason": "invalid_json"}

        # 빈 payload 처리
        if not payload:
            logger.warning("⚠️ Empty payload received")
            return {"status": "ignored", "reason": "empty_payload"}

        # 웹훅 카테고리 확인
        category = payload.get("category")
        logger.info(f"📂 [WEBHOOK-DEBUG] Category: {category}")

        if category == "group_channel:message_send":
            logger.info("✅ [WEBHOOK-DEBUG] Processing message_send event...")
            # 메시지 전송 이벤트
            await handle_message_send(payload, background_tasks)
        else:
            logger.warning(f"⚠️ [WEBHOOK-DEBUG] Unhandled category: {category}")

        logger.info("=" * 80)
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        logger.error(f"   Stack trace:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def handle_message_send(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """메시지 전송 이벤트 처리"""
    try:
        logger.info("📨 [WEBHOOK-DEBUG] Parsing message payload...")

        # 페이로드 파싱
        channel_url = payload.get("channel", {}).get("channel_url")
        sender = payload.get("sender", {})
        sender_id = sender.get("user_id")
        message = payload.get("payload", {}).get("message", "")

        logger.info(f"   Channel URL: {channel_url}")
        logger.info(f"   Sender ID: {sender_id}")
        logger.info(f"   Message: {message}")
        logger.info(f"   AI User ID: {SendbirdConfig.AI_USER_ID}")

        # AI 자신의 메시지는 무시
        if sender_id == SendbirdConfig.AI_USER_ID:
            logger.info("⏭️  [WEBHOOK-DEBUG] Ignoring AI's own message")
            return

        logger.info(f"✅ [WEBHOOK-DEBUG] Processing user message from {sender_id}: {message}")

        # 메모리에 추가
        memory_service.add_message(sender_id, "user", message)
        logger.info("💾 [WEBHOOK-DEBUG] Message added to memory")

        # 백그라운드에서 응답 생성 및 전송
        logger.info("🚀 [WEBHOOK-DEBUG] Adding background task for response generation...")
        background_tasks.add_task(
            process_and_respond,
            channel_url,
            sender_id,
            message
        )
        logger.info("✅ [WEBHOOK-DEBUG] Background task added successfully")

    except Exception as e:
        logger.error(f"❌ Message handling error: {str(e)}")
        logger.error(f"   Stack trace:", exc_info=True)


async def process_and_respond(
    channel_url: str,
    user_id: str,
    message: str
):
    """메시지 처리 및 응답"""
    try:
        logger.info("=" * 80)
        logger.info("🤖 [RESPONSE-DEBUG] Starting AI response generation...")
        logger.info(f"   User: {user_id}")
        logger.info(f"   Message: {message}")
        logger.info(f"   Channel: {channel_url}")

        # 대화 히스토리 조회
        history = memory_service.get_history(user_id)
        logger.info(f"📚 [RESPONSE-DEBUG] Retrieved {len(history)} messages from history")

        # 장기 메모리 조회 (사용자 정보, 선호도 등)
        long_term = memory_service.get_long_term_memory(user_id)
        logger.info(f"💭 [RESPONSE-DEBUG] Long-term memory: {long_term.get('persona', 'default')}")

        # LLM 응답 생성
        logger.info("🧠 [RESPONSE-DEBUG] Generating LLM response...")
        response = await llm_service.generate_response(
            user_message=message,
            conversation_history=history,
            persona=long_term.get("persona"),
            context={
                "user_id": user_id,
                "channel_url": channel_url
            }
        )

        action = response.get("action", "NONE")
        response_text = response.get("response", "")
        logger.info(f"✅ [RESPONSE-DEBUG] LLM response generated!")
        logger.info(f"   Action: {action}")
        logger.info(f"   Response: {response_text[:100]}...")

        # 메모리에 AI 응답 추가
        memory_service.add_message(user_id, "assistant", response_text)
        logger.info("💾 [RESPONSE-DEBUG] AI response saved to memory")

        # 액션 처리
        if action == LLMAction.NONE:
            # 일반 텍스트 응답
            logger.info("📤 [RESPONSE-DEBUG] Sending text response via Sendbird...")
            await chat_client.send_message(
                channel_url=channel_url,
                message=response_text,
                user_id=user_id
            )
            logger.info(f"✅ [RESPONSE-DEBUG] Text response sent to {user_id} successfully!")
            logger.info("=" * 80)

        elif action == LLMAction.CALL:
            # 전화 걸기
            # 먼저 메시지 전송
            await chat_client.send_message(
                channel_url=channel_url,
                message=response_text,
                user_id=user_id
            )

            # 전화 발신
            await calls_client.make_call(
                caller_id=SendbirdConfig.AI_USER_ID,
                callee_id=user_id,
                call_type="voice"
            )
            logger.info(f"📞 Call initiated to {user_id}")

        elif action == LLMAction.AUTO_CALL:
            # 자동 전화 (GPS 트리거)
            message_to_user = response.get("message_to_user", response_text)

            # 메시지 먼저 전송
            await chat_client.send_message(
                channel_url=channel_url,
                message=message_to_user,
                user_id=user_id
            )

            # 전화 발신
            await calls_client.make_call(
                caller_id=SendbirdConfig.AI_USER_ID,
                callee_id=user_id,
                call_type="voice"
            )
            logger.info(f"📞 Auto-call initiated to {user_id}")
    
    except Exception as e:
        logger.error(f"❌ Process and respond error: {str(e)}")

        # 에러 메시지 전송
        try:
            await chat_client.send_message(
                channel_url=channel_url,
                message="죄송해요, 일시적인 오류가 발생했어요. 잠시 후 다시 시도해주세요.",
                user_id=user_id
            )
        except:
            pass


@router.post("/calls")
async def sendbird_calls_webhook(request: Request):
    """
    Sendbird Calls 웹훅 수신

    Webhook 설정:
    - Dashboard > Calls > Settings > Webhooks
    - Events: call.ended, call.established 등
    """
    try:
        # JSON 파싱 에러 처리
        try:
            payload = await request.json()
        except Exception as json_error:
            logger.warning(f"⚠️ Invalid JSON in calls webhook request: {str(json_error)}")
            return {"status": "ignored", "reason": "invalid_json"}

        # 빈 payload 처리
        if not payload:
            logger.warning("⚠️ Empty payload received in calls webhook")
            return {"status": "ignored", "reason": "empty_payload"}

        event_type = payload.get("type")
        call_id = payload.get("call_id")

        logger.info(f"📞 Calls webhook: {event_type} - {call_id}")

        # 통화 종료 시 요약 생성 등
        if event_type == "call.ended":
            await handle_call_ended(payload)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"❌ Calls webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_call_ended(payload: Dict[str, Any]):
    """통화 종료 처리"""
    try:
        call_id = payload.get("call_id")
        duration = payload.get("duration", 0)
        
        # TODO: 통화 내용 요약, 메모리 업데이트 등
        logger.info(f"📴 Call ended: {call_id}, duration: {duration}s")
    
    except Exception as e:
        logger.error(f"❌ Call ended handling error: {str(e)}")


