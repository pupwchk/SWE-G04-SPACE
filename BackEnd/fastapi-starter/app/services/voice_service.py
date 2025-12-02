"""
음성 처리 서비스 - STT, TTS, 실시간 음성 대화
"""
import os
import logging
from typing import AsyncIterator, Optional
from openai import AsyncOpenAI
import base64

logger = logging.getLogger(__name__)

# OpenAI 클라이언트
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


class VoiceService:
    """음성 처리 서비스"""
    
    def __init__(self):
        self.stt_model = "whisper-1"
        self.tts_model = "tts-1"  # 빠른 응답용, tts-1-hd는 고품질
        self.tts_voice = "alloy"  # alloy, echo, fable, onyx, nova, shimmer
    
    async def speech_to_text(
        self,
        audio_data: bytes,
        language: str = "ko"
    ) -> str:
        """
        음성을 텍스트로 변환 (STT)
        
        Args:
            audio_data: 오디오 데이터 (bytes)
            language: 언어 코드
        
        Returns:
            텍스트
        """
        try:
            # Whisper API 호출
            # 실제로는 파일 객체를 전달해야 함
            from io import BytesIO
            audio_file = BytesIO(audio_data)
            audio_file.name = "audio.wav"
            
            response = await client.audio.transcriptions.create(
                model=self.stt_model,
                file=audio_file,
                language=language
            )
            
            text = response.text
            logger.info(f"✅ STT: {text[:50]}...")
            return text
            
        except Exception as e:
            logger.error(f"❌ STT error: {str(e)}")
            raise
    
    async def text_to_speech(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> bytes:
        """
        텍스트를 음성으로 변환 (TTS)
        
        Args:
            text: 텍스트
            voice: 음성 종류 (alloy, echo, fable, onyx, nova, shimmer)
        
        Returns:
            오디오 데이터 (bytes)
        """
        try:
            if voice is None:
                voice = self.tts_voice
            
            response = await client.audio.speech.create(
                model=self.tts_model,
                voice=voice,
                input=text,
                response_format="opus"  # opus, mp3, aac, flac
            )
            
            audio_data = response.content
            logger.info(f"✅ TTS: Generated {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"❌ TTS error: {str(e)}")
            raise
    
    async def text_to_speech_stream(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> AsyncIterator[bytes]:
        """
        텍스트를 음성으로 변환 (스트리밍)
        
        Args:
            text: 텍스트
            voice: 음성 종류
        
        Yields:
            오디오 청크
        """
        try:
            if voice is None:
                voice = self.tts_voice
            
            response = await client.audio.speech.create(
                model=self.tts_model,
                voice=voice,
                input=text,
                response_format="opus"
            )
            
            # 스트리밍 응답
            async for chunk in response.iter_bytes(chunk_size=4096):
                yield chunk
            
            logger.info(f"✅ TTS streaming completed")
            
        except Exception as e:
            logger.error(f"❌ TTS streaming error: {str(e)}")
            raise


class RealtimeVoiceService:
    """
    실시간 음성 대화 서비스
    OpenAI Realtime API 사용
    """
    
    def __init__(self):
        self.model = "gpt-realtime"
    
    async def create_realtime_session(
        self,
        system_prompt: str,
        voice: str = "alloy"
    ):
        """
        실시간 음성 세션 생성
        
        Note: OpenAI Realtime API는 WebSocket 기반
        실제 구현은 WebSocket 연결 필요
        """
        # TODO: Realtime API WebSocket 구현
        # https://platform.openai.com/docs/guides/realtime
        pass
    
    async def process_audio_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        system_prompt: str
    ) -> AsyncIterator[bytes]:
        """
        실시간 오디오 스트림 처리
        
        Args:
            audio_stream: 입력 오디오 스트림
            system_prompt: 시스템 프롬프트
        
        Yields:
            출력 오디오 스트림
        """
        # 실시간 처리 파이프라인:
        # 1. 오디오 청크 수신
        # 2. STT (Whisper)
        # 3. LLM 응답 생성
        # 4. TTS
        # 5. 오디오 청크 전송
        
        # 간단한 구현 (실시간은 아님)
        voice_service = VoiceService()
        from app.services.llm_service import llm_service
        
        try:
            # 오디오 버퍼
            audio_buffer = bytearray()
            
            async for chunk in audio_stream:
                audio_buffer.extend(chunk)
                
                # 일정 크기 이상이면 처리
                if len(audio_buffer) >= 16000:  # ~1초 분량
                    # STT
                    text = await voice_service.speech_to_text(bytes(audio_buffer))
                    
                    if text.strip():
                        # LLM 응답
                        response = await llm_service.generate_response(
                            user_message=text,
                            conversation_history=None,
                            persona=None,
                            context=None
                        )
                        
                        response_text = response.get("response", "")
                        
                        # TTS
                        audio_response = await voice_service.text_to_speech(response_text)
                        
                        # 응답 전송
                        yield audio_response
                    
                    # 버퍼 초기화
                    audio_buffer.clear()
        
        except Exception as e:
            logger.error(f"❌ Realtime audio processing error: {str(e)}")
            raise


# 싱글톤 인스턴스
voice_service = VoiceService()
realtime_voice_service = RealtimeVoiceService()
