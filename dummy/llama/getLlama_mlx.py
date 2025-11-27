from mlx_lm import load, generate
import time

print("=" * 60)
print("MLX 버전 - Apple Silicon 전용 초고속 모드")
print("=" * 60)

# MLX 호환 한국어 모델
model_name = "mlx-community/Llama-3.2-3B-Instruct-4bit"  # 3B, 4bit 양자화

print(f"\n모델 로딩 중: {model_name}")
print("(첫 실행 시 자동 다운로드됩니다)")
start = time.time()

model, tokenizer = load(model_name)

print(f"✅ 로딩 완료! ({time.time() - start:.1f}초)")
print("=" * 60)

def chat(user_message, max_tokens=100):
    """MLX 초고속 채팅"""
    print(f"\n질문: {user_message}")

    # Llama 3 형식 프롬프트
    prompt = f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>

{user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

    start = time.time()
    response = generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=max_tokens,
        verbose=False  # 진행 상황 숨김
    )
    elapsed = time.time() - start

    # 응답 정리
    answer = response.strip()
    if "<|eot_id|>" in answer:
        answer = answer.split("<|eot_id|>")[0].strip()

    # 토큰 수 추정
    tokens = len(answer.split())
    speed = tokens / elapsed if elapsed > 0 else 0

    print(f"답변: {answer}")
    print(f"⚡ {elapsed:.2f}초 | ~{speed:.1f} tokens/sec")

    return answer

# 사용 예제
if __name__ == "__main__":
    print("\n[빠른 테스트]\n")

    chat("안녕하세요!", max_tokens=50)
    chat("Python이란 무엇인가요?", max_tokens=100)

    print("\n" + "=" * 60)
    print("대화 모드 (종료: quit)")
    print("=" * 60)

    while True:
        user_input = input("\n> ")
        if user_input.lower() in ['quit', 'exit', 'q', '종료']:
            print("종료합니다.")
            break

        if not user_input.strip():
            continue

        chat(user_input, max_tokens=150)
