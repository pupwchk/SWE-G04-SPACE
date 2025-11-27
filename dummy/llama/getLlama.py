from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_id = "allganize/Llama-3-Alpha-Ko-8B-Instruct"

print("토크나이저 로딩 중...")
tokenizer = AutoTokenizer.from_pretrained(model_id, token="Your_Token")

print("모델 로딩 중 (CPU 모드)...")

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    dtype=torch.float32,  # CPU에서는 float32 사용
    token="Your_Token",
    low_cpu_mem_usage=True
)

print("모델 로딩 완료! (CPU 모드)")
print(f"디바이스: {model.device}")
print(f"Dtype: {model.dtype}")
print("⚠️ CPU 모드는 느립니다. 작은 모델 권장.")

# 대화형 함수
def chat(user_message, system_prompt="당신은 친절한 AI 어시스턴트입니다."):
    print(f"[처리중] '{user_message[:30]}...' 답변 생성 중...")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    # 템플릿 적용
    input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

    print(f"[입력 토큰 수] {inputs['input_ids'].shape[1]}")

    # 생성 (최대 속도 최적화)
    import time
    start_time = time.time()

    outputs = model.generate(
        **inputs,
        max_new_tokens=64,  # 128 -> 64로 더 줄임 (2배 빠름)
        do_sample=False,  # Greedy decoding (샘플링 끄면 더 빠름)
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        use_cache=True,
        num_beams=1  # Beam search 비활성화
    )

    elapsed = time.time() - start_time
    print(f"[생성 완료] {elapsed:.2f}초 소요, {outputs.shape[1]} 토큰 생성")

    # 디코딩
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # 응답 부분만 추출
    if "assistant" in response:
        response = response.split("assistant")[-1].strip()

    return response

# 사용 예제
if __name__ == "__main__":
    # 예제 1: 간단한 질문
    print("\n=== 예제 1 ===")
    response = chat("안녕하세요! 오늘 날씨가 어때요?")
    print(f"AI: {response}")

    # 예제 2: 코드 설명
    print("\n=== 예제 2 ===")
    response = chat("Python의 리스트 컴프리헨션을 설명해주세요.")
    print(f"AI: {response}")

    # 예제 3: 대화형 루프
    print("\n=== 대화 시작 (종료하려면 'quit' 입력) ===")
    while True:
        user_input = input("\n사용자: ")
        if user_input.lower() in ['quit', 'exit', '종료']:
            print("대화를 종료합니다.")
            break

        response = chat(user_input)
        print(f"AI: {response}")