import openai

openai.api_base = "http://localhost:8084/v1"
openai.api_key = "E"
response = openai.Completion.create(
    model="Qwen2.5-3B-SFT-GRPO-2000",
    prompt="If Olivia eats 2 eggs a day for 83 days and then increases it to 5 eggs a day for 58 days, how many dozens of eggs will Olivia need for 141 days? Please help me to",
    temperature=0,
    max_tokens=20000,
    stop=None,
    stream=False
)

print(response.choices[0].text.strip())