"""
Voice API
실시간 음성 처리 (STT/TTS)
"""
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.services.voice_service import voice_service
from app.services.llm_service import llm_service, memory_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["Voice"])


class TTSRequest(BaseModel):
    """TTS 요청"""
    text: str
    voice: Optional[str] = "alloy"  # alloy, echo, fable, onyx, nova, shimmer
    user_id: Optional[str] = None


@router.post("/stt")
async def speech_to_text(
    audio: UploadFile = File(...),
    user_id: Optional[str] = None,
    language: str = "ko"
):
    """
    음성을 텍스트로 변환 (STT)
    
    Args:
        audio: 오디오 파일 (wav, mp3, m4a 등)
        user_id: 사용자 ID (옵션)
        language: 언어 코드
    """
    try:
        # 오디오 데이터 읽기
        audio_data = await audio.read()
        
        # STT 처리
        text = await voice_service.speech_to_text(audio_data, language)
        
        logger.info(f"✅ STT result: {text[:100]}")
        
        return {
            "text": text,
            "language": language
        }
    
    except Exception as e:
        logger.error(f"❌ STT error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    텍스트를 음성으로 변환 (TTS)
    
    Returns:
        오디오 스트림 (audio/opus)
    """
    try:
        # TTS 처리
        audio_data = await voice_service.text_to_speech(
            text=request.text,
            voice=request.voice
        )
        
        logger.info(f"✅ TTS generated: {len(audio_data)} bytes")
        
        # 오디오 스트림 반환
        return StreamingResponse(
            iter([audio_data]),
            media_type="audio/opus",
            headers={
                "Content-Disposition": "attachment; filename=speech.opus"
            }
        )
    
    except Exception as e:
        logger.error(f"❌ TTS error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts/stream")
async def text_to_speech_stream(request: TTSRequest):
    """
    텍스트를 음성으로 변환 (스트리밍)
    
    Returns:
        오디오 스트림
    """
    try:
        async def audio_generator():
            async for chunk in voice_service.text_to_speech_stream(
                text=request.text,
                voice=request.voice
            ):
                yield chunk
        
        return StreamingResponse(
            audio_generator(),
            media_type="audio/opus"
        )
    
    except Exception as e:
        logger.error(f"❌ TTS streaming error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation")
async def voice_conversation(
    audio: UploadFile = File(...),
    user_id: str = "default_user",
    language: str = "ko"
):
    """
    음성 대화 처리 (STT → LLM → TTS)
    
    전체 파이프라인:
    1. 음성 → 텍스트 (STT)
    2. LLM 응답 생성
    3. 텍스트 → 음성 (TTS)
    
    Returns:
        오디오 응답
    """
    try:
        # 1. STT
        audio_data = await audio.read()
        user_text = await voice_service.speech_to_text(audio_data, language)
        
        logger.info(f"👤 User said: {user_text}")
        
        # 2. 메모리에 추가
        memory_service.add_message(user_id, "user", user_text)
        
        # 3. LLM 응답 생성
        history = memory_service.get_history(user_id)
        long_term = memory_service.get_long_term_memory(user_id)
        
        response = await llm_service.generate_response(
            user_message=user_text,
            conversation_history=history,
            persona=long_term.get("persona"),
            context={"user_id": user_id, "mode": "voice"}
        )
        
        response_text = response.get("response", "")
        logger.info(f"🤖 AI response: {response_text}")
        
        # 4. 메모리에 추가
        memory_service.add_message(user_id, "assistant", response_text)
        
        # 5. TTS
        audio_response = await voice_service.text_to_speech(
            text=response_text,
            voice=long_term.get("voice", "alloy")
        )
        
        # 6. 오디오 반환
        return StreamingResponse(
            iter([audio_response]),
            media_type="audio/opus",
            headers={
                "X-Response-Text": response_text,
                "X-Action": response.get("action", "NONE")
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Voice conversation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/realtime")
async def realtime_voice_conversation(websocket):
    """
    실시간 음성 대화 (WebSocket)
    
    TODO: WebSocket 기반 실시간 음성 처리
    - 클라이언트가 오디오 청크를 계속 전송
    - 서버가 실시간으로 STT → LLM → TTS 처리
    - 응답 오디오 청크를 실시간으로 전송
    """
    await websocket.accept()
    
    try:
        while True:
            # 오디오 청크 수신
            data = await websocket.receive_bytes()
            
            # TODO: 실시간 처리
            # 1. VAD (Voice Activity Detection)
            # 2. STT
            # 3. LLM
            # 4. TTS
            # 5. 응답 전송
            
            await websocket.send_bytes(b"")
    
    except Exception as e:
        logger.error(f"❌ WebSocket error: {str(e)}")
    finally:
        await websocket.close()


