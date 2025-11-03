import openai
import tempfile
import os
from pydub import AudioSegment

# OpenAI API Key 설정
openai.api_key = ""  # 개인 키 입력

# 시스템 프롬프트 설정
SYSTEM_PROMPT = """
너는 병원 진료과 추천을 담당하는 챗봇이다.
사용자의 증상을 보고 가장 적절한 진료과를 '한 단어'로만 출력해라.
설명, 문장, 병명 언급은 절대 하지 말고, 오직 진료과 이름(예: 내과, 정형외과, 이비인후과, 피부과 등)만 출력한다.
"""

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


# 응급 / 소아 상황 선처리
def preprocess_input(user_text):
    text = user_text.lower()

    emergency_keywords = ["피", "출혈", "호흡", "숨", "의식", "심장", "쓰러졌", "경련", "응급"]
    child_keywords = ["아이", "어린이", "아기", "소아", "유아", "초등학생"]

    if any(word in text for word in emergency_keywords):
        return "응급실"
    elif any(word in text for word in child_keywords):
        return "소아청소년과"
    else:
        return None


# GPT 응답 함수 (진료과명 단어만 반환)
def get_chat_response(user_text):
    preprocessed = preprocess_input(user_text)
    if preprocessed:
        return preprocessed

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
    )

    answer = response.choices[0].message.content.strip()

    # 혹시 문장이 섞여 있을 경우 첫 단어만 추출
    if " " in answer:
        answer = answer.split()[0]

    return answer


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
            print(f"추천 진료과: {reply}\n")

        elif mode == "2":
            audio_path = input("음성 파일 경로 입력 (예: test.wav): ").strip()
            if not os.path.exists(audio_path):
                print("파일을 찾을 수 없습니다.\n")
                continue
            text = speech_to_text(audio_path)
            print(f"음성 인식 결과: {text}")
            reply = get_chat_response(text)
            print(f"추천 진료과: {reply}\n")

        else:
            print("잘못된 입력입니다. 1 또는 2를 선택하세요.\n")


if __name__ == "__main__":
    run_chatbot()
