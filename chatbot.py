from flask import Flask, request, jsonify
import openai
import tempfile
import os
import base64
import io
from pydub import AudioSegment

app = Flask(__name__)

# ① OpenAI API Key
openai.api_key = ""  # personal key

# ② 일시적 로그 저장용 메모리 버퍼
chat_logs = []  # [(user_text, bot_reply), ...]

# ③ 텍스트 입력 + 음성 입력 모두 지원
@app.route("/chatbot", methods=["POST"])
def chatbot():
    user_text = ""
    
    # JSON 또는 multipart/form-data 지원
    if "text" in request.form:
        user_text = request.form["text"]
    elif request.is_json:
        data = request.get_json()
        user_text = data.get("text", "")
    elif "audio" in request.files:
        audio_file = request.files["audio"]
        user_text = speech_to_text(audio_file)
    else:
        return jsonify({"error": "입력값이 없습니다."}), 400

    # GPT 응답 생성
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "너는 병원 조언 챗봇이야. 사용자가 증상을 입력하면 병명에 대해 언급하지 말고 진료과 이름만 알려줘."},
            {"role": "user", "content": user_text}
        ]
    )
    bot_reply = response.choices[0].message.content

    # 로그 저장 (일시적 버퍼)
    chat_logs.append((user_text, bot_reply))

    print(f"[사용자 입력] {user_text}")
    print(f"[챗봇 응답] {bot_reply}")

    return jsonify({"user": user_text, "bot": bot_reply})


# ④ 음성 → 텍스트 변환 함수
def speech_to_text(audio_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        audio = AudioSegment.from_file(audio_file)
        audio.export(temp_audio.name, format="wav")
        temp_audio_path = temp_audio.name

    with open(temp_audio_path, "rb") as f:
        transcript = openai.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f
        )
    os.remove(temp_audio_path)
    return transcript.text


# ⑤ 로그 확인용 임시 API (테스트용)
@app.route("/logs", methods=["GET"])
def get_logs():
    return jsonify({"logs": chat_logs})


if __name__ == "__main__":
    app.run(debug=True)
