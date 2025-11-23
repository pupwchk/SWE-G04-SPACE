from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import time

# 더 작은 모델 사용 (2B - 8B보다 4배 빠름)
model_id = "beomi/Llama-3-Open-Ko-8B-Instruct-preview"  # 또는 다른 작은 모델

print("=" * 60)
print("빠른 버전: 작은 모델 + 최대 속도 최적화")
print("=" * 60)

print("\n토크나이저 로딩 중...")
tokenizer = AutoTokenizer.from_pretrained(model_id)

print("모델 로딩 중...")
start_load = time.time()

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True
)

print(f"모델 로딩 완료! ({time.time() - start_load:.1f}초)")
print(f"디바이스: {model.device}")
print("=" * 60)

def chat(user_message):
    """초고속 채팅 함수"""
    print(f"\n질문: {user_message}")

    # 간단한 프롬프트 (템플릿 오버헤드 제거)
    prompt = f"질문: {user_message}\n답변:"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    start = time.time()
    outputs = model.generate(
        **inputs,
        max_new_tokens=50,  # 짧게
        do_sample=False,  # Greedy
        pad_token_id=tokenizer.eos_token_id
    )
    elapsed = time.time() - start

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # 답변 부분만 추출
    if "답변:" in response:
        response = response.split("답변:")[-1].strip()

    tokens_generated = outputs.shape[1] - inputs['input_ids'].shape[1]
    speed = tokens_generated / elapsed if elapsed > 0 else 0

    print(f"답변: {response}")
    print(f"⚡ 생성 시간: {elapsed:.2f}초 | 속도: {speed:.1f} tokens/sec")

    return response

# 빠른 테스트
if __name__ == "__main__":
    print("\n[빠른 테스트 모드]\n")

    chat("안녕")
    chat("Python이란?")
    chat("1+1은?")

    print("\n" + "=" * 60)
    print("대화 모드 (종료: quit)")
    print("=" * 60)

    while True:
        user_input = input("\n> ")
        if user_input.lower() in ['quit', 'exit', '종료', 'q']:
            break
        chat(user_input)
