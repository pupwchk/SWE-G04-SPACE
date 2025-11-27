#!/bin/bash
# 음성 파일을 S2S 테스트용 형식으로 변환
# 사용법: ./convert_audio.sh input.mp3 output.wav

if [ $# -lt 2 ]; then
    echo "사용법: $0 <입력파일> <출력파일>"
    echo "예시: $0 input.mp3 output.wav"
    exit 1
fi

INPUT="$1"
OUTPUT="$2"

if [ ! -f "$INPUT" ]; then
    echo "❌ 입력 파일을 찾을 수 없습니다: $INPUT"
    exit 1
fi

echo "🔄 음성 파일 변환 중..."
echo "   입력: $INPUT"
echo "   출력: $OUTPUT (PCM16, 16kHz, Mono)"

# ffmpeg가 설치되어 있는지 확인
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg가 설치되어 있지 않습니다."
    echo ""
    echo "설치 방법:"
    echo "  macOS: brew install ffmpeg"
    echo "  Ubuntu: sudo apt install ffmpeg"
    exit 1
fi

# 변환 실행
ffmpeg -i "$INPUT" -ar 16000 -ac 1 -sample_fmt s16 "$OUTPUT" -y

if [ $? -eq 0 ]; then
    echo "✅ 변환 완료: $OUTPUT"

    # 파일 정보 출력
    if command -v ffprobe &> /dev/null; then
        echo ""
        echo "📊 변환된 파일 정보:"
        ffprobe -v error -show_entries stream=sample_rate,channels,bits_per_sample -of default=noprint_wrappers=1 "$OUTPUT"
    fi
else
    echo "❌ 변환 실패"
    exit 1
fi
