import openai

# ① API key (Don't touch!!)
openai.api_key = "xxxxxxxxxxxxxxxxxxxxxx"  # personal key!! DO NOT UPLOAD HERE! check PC

# chatbot messages
response = openai.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "너는 병원 조언 챗봇이야. 사용자가 증상을 입력하면 병명에 대해 언급하지 말고 진료과 이름만 알려줘."},
        {"role": "user", "content": "배가 아프고 메스꺼워요."}
    ]
)

reply = response.choices[0].message.content
print("챗봇:", reply)
