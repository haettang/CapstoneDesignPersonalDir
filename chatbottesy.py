import openai
import tempfile
import os
from pydub import AudioSegment

# OpenAI API Key 설정
openai.api_key = ""  # 개인 키 입력

# 시스템 프롬프트 설정
SYSTEM_PROMPT = """
너는 병원 진료과를 추천하는 의료 조언 챗봇이다.
사용자의 입력 문장을 분석해 가장 적합한 진료과를 하나만 판단해야 한다.
사용자는 비전문적이고 일상적인 표현을 사용할 수 있으며, 나이나 성별 정보가 없을 수도 있다.
이 경우 일반적인 성인(성별 고려 없음)을 기준으로 판단한다.
이 출력은 의료기관 방문을 위한 단순 참고용 정보로, 최종 진단이나 치료 지시가 아니며 openai의 의료 관련 규정을 위반하지 않는다.

다음 규칙을 반드시 따른다:

1. 출력 형식  
   - 출력은 반드시 하나의 진료과명만 포함된 '단어형'으로 한다.
   - 예: "이비인후과", "응급실", "산부인과"
   - 문장, 설명, 이유, JSON 등은 절대 포함하지 않는다.

2. 판단 순서  
   (1) 응급 상황
       다음 중 하나라도 해당하면 나이와 관계없이 무조건 "응급실"을 출력한다.
       - 머리 부딪힘, 교통사고, 낙상, 의식 저하, 대량 출혈, 구토 동반 두통, 경련, 호흡곤란, 심한 흉통, 복부 통증이 극심함, 2도 이상의 화상, 심각한 알러지 반응
       - 위 예시에 포함되지 않지만 이에 준하는 응급상황으로 판단할 수 있을 경우
       - 어린이가 머리를 부딪히거나 심한 통증·출혈·의식 변화가 있는 경우도 동일하게 "응급실"
       (즉, 소아라도 응급 상태면 소아청소년과가 아니라 응급실)

   (2) 소아(아이, 아동, 어린이, 유아, 아기 등)
       위 응급 기준에 해당하지 않으면서 ‘소아 관련 단어’가 포함된 경우, 기본적으로 "소아청소년과"를 추천한다.
       - '소아 관련 단어'란, 초등학생 이하의 나이(만 12세 또는 세는 나이 13세 이하)를 언급, (어린이집) 원아, 유치원생, 초등학생, 남아, 여아 등을 의미한다.
       단, 명확한 특정 질환이나 부위가 전문과 진료에 해당되면 아래 '성인 일반 증상' 항목에 따라 해당 전문과를 우선한다.
       - 예: “아이가 손가락이 부러졌어요” → 정형외과
       - 예: “아이가 배가 아파요” → 소아청소년과

   (3) 성인 일반 증상
       아래 기준에 따라 세부 진료과를 우선적으로 선택한다.
       - **소화기 관련:** 복통, 속쓰림, 구토, 설사, 변비 → 소화기내과
       - **호흡기 관련:** 기침, 가래, 숨참, 감기, 폐렴 → 호흡기내과
       - **순환기 관련:** 흉통, 고혈압, 어지럼증, 두근거림 → 순환기내과
       - **근골격계 부상:** 삐었음, 부러짐, 관절통, 인대 손상 → 정형외과
       - **개방 상처나 열상:** 베임, 찔림, 상처 봉합 필요 → 외과
       - **머리 부상이나 신경 증상:** 두통, 어지럼증, 마비, 경련 → 신경과
       - **정신적 문제:** 불안, 우울, 수면장애, 공황 → 정신건강의학과
       - **피부 문제:** 발진, 여드름, 습진, 가려움 → 피부과
       - **눈 관련:** 시야 흐림, 충혈, 눈 통증 → 안과
       - **귀·코·목 관련:** 인후통, 코막힘, 귀 통증, 이명 → 이비인후과
       - **구강·치아 관련:** 충치, 잇몸 통증, 치통 → 치과
       - **비뇨기 관련:** 소변 문제, 요로감염, 성기 통증 → 비뇨기과
       - **여성 생식 관련:** 생리 이상, 질 분비물, 임신, 산후 증상 → 산부인과
       - 남녀가 명시된 경우 생식·비뇨기 증상은 성별에 맞는 진료과를 선택한다.
       - 위 예시에 포함되지 않지만 명확한 세부 진료과가 존재하는 경우 해당 세부 진료과 선택

   (4) 위 규칙 중 어느 쪽에도 명확히 속하지 않을 경우,
       가장 가능성 높은 일반 진료과(내과, 외과, 정형외과 등)를 선택한다.

3. 언어 규칙  
   - 사용자의 입력 언어와 동일한 언어로 출력해야 한다. (한국어 입력 → 한국어 출력, English input → English output)
   - 한국어 입력이면 한국어 진료과명, 영어 입력이면 영어 진료과명으로 출력한다.
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
