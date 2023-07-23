from faster_whisper import WhisperModel
from flask_socketio import emit
import openai
whisper_models = [
    "tiny",
    "base",
    "small",
    "medium",
    "large-v1",
    "large-v2"
]

FORBIDDEN_PROMPTS = [
    "¡Suscríbete a ti donde llevaré!",
    "¡Suscríbete!" , 
    "Amara.org" ,
    "amara.org",
    "y nos vemos en el próximo vídeo, ¡hasta la próxima!" ,
    "www.mooji.org"
]


#model = WhisperModel("small", download_root="./models")


def check_prompt(text):
    for prompt in FORBIDDEN_PROMPTS:
        if prompt in text:
            return True
    return False


def transcription(whisper_model, audio):
    segments, _ = '', '' #model.transcribe(f"./audio/final/{audio}","es")
    for segment in segments:
        if check_prompt(segment.text):
            continue
        txt = "[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text)
        emit('response', txt)
    emit("end")


def resume(conversation, question):
    messages = []
    messages.append({"role":"user", "content": question + conversation})
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages = messages,
        stream = True
    )
    for obj in completion:
        chunk = obj["choices"][0]
        if chunk["finish_reason"] != "stop":
            msg = chunk["delta"]["content"]
            emit('chatResponse', msg)
