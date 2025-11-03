import openai
import tempfile
import os
from pydub import AudioSegment

# OpenAI API Key 설정
openai.api_key = ""  # 개인 키 입력

# 병원 조언 챗봇 프롬프트
SYSTEM_PROMPT = "너는 병원 조언 챗봇이야. 사용자가 증상을 입력하면 병명에 대해 언급하지 말고 진료과 이름만 알려줘."


# 음성 → 텍스트 변환 함수
def speech_to_text(audio_path):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        audio = AudioSegment.from_file(audio_path)
        audio.export(temp_audio.name, format="wav")
        temp_audio_path = temp_audio.name

    with open(temp_audio_path, "rb") as f:
        transcript = openai.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f
        )
    os.remove(temp_audio_path)
    return transcript.text


# 챗봇 응답 함수
def get_chat_response(user_text):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
    )
    return response.choices[0].message.content


# 터미널 테스트용 메인 함수
def run_chatbot():
    print("병원 진료과 추천 챗봇 (종료하려면 exit 입력)\n")
    while True:
        mode = input("텍스트 입력은 1, 음성 파일 입력은 2를 선택: ").strip()

        if mode == "1":
            user_input = input("사용자 입력: ")
            if user_input.lower() in ["exit", "quit", "종료"]:
                print("챗봇을 종료합니다.")
                break
            reply = get_chat_response(user_input)
            print(f"챗봇 응답: {reply}\n")

        elif mode == "2":
            audio_path = input("음성 파일 경로 입력 (예: test.wav): ").strip()
            if not os.path.exists(audio_path):
                print("파일을 찾을 수 없습니다.\n")
                continue
            text = speech_to_text(audio_path)
            print(f"음성 인식 결과: {text}")
            reply = get_chat_response(text)
            print(f"챗봇 응답: {reply}\n")

        else:
            print("잘못된 입력입니다. 1 또는 2를 선택하세요.\n")


if __name__ == "__main__":
    run_chatbot()
