from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import time

print("=" * 50)
print("모델 로딩 시작...")
start = time.time()

model_id = "allganize/Llama-3-Alpha-Ko-8B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_id, token="Your_Token")
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.float16,  # 명시적으로 float16 지정
    token="Your_Token"
)

print(f"모델 로딩 완료! ({time.time() - start:.2f}초)")
print(f"디바이스: {model.device}")
print(f"모델 dtype: {model.dtype}")
print("=" * 50)

# 간단한 테스트
def quick_test(prompt):
    print(f"\n질문: {prompt}")
    print("생성 중...", end="", flush=True)

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    start = time.time()
    outputs = model.generate(
        **inputs,
        max_new_tokens=50,  # 짧게 테스트
        do_sample=False,  # greedy decoding (더 빠름)
        pad_token_id=tokenizer.eos_token_id
    )
    elapsed = time.time() - start

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f" 완료! ({elapsed:.2f}초)")
    print(f"답변: {response}\n")

    return elapsed

# 테스트 실행
print("\n[테스트 1] 간단한 질문")
quick_test("안녕")

print("\n[테스트 2] 조금 더 긴 질문")
quick_test("Python이란 무엇인가요?")

print("\n" + "=" * 50)
print("테스트 완료!")
