from faster_whisper import WhisperModel
from flask_socketio import emit
import openai
from flask import request, session
import time
from datetime import datetime
from audio import delTrash, mergeAudios, saveAudio, saveMic
import os

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


model = WhisperModel("small", download_root="./models")


def check_prompt(text):
    for prompt in FORBIDDEN_PROMPTS:
        if prompt in text:
            return True
    return False


def transcribe(path):
    segments, _ =  model.transcribe(path,"es")
    for segment in segments:
        if check_prompt(segment.text):
            continue
        txt = "[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text)
        emit('response', txt, to=request.sid)


def transcription(whisper_model, audio):
    user = session['user']
    transcribe(f"./audio/final/{user}/{audio}")
    emit("end", to=request.sid)


def resume(conversation, question):
    messages = []
    messages.append({"role":"user", "content": question + conversation})
    openai.organization = os.getenv("OPENAI_ORG")
    openai.api_key = os.getenv("OPENAI_API_KEY")
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages = messages,
        stream = True
    )
    for obj in completion:
        chunk = obj["choices"][0]
        if chunk["finish_reason"] != "stop":
            msg = chunk["delta"]["content"]
            emit('chatResponse', msg, to=request.sid)


def real_time(record_chunks, mic_chunks):
    seconds = 0
    while session['realTime']:
        if (seconds < 5):
            time.sleep(5 - seconds)
        saveAudio(record_chunks)
        saveMic(mic_chunks)
        audio = mergeAudios()
        start_time = datetime.now()
        transcribe(audio)
        final_time = datetime.now()
        seconds = (final_time - start_time).seconds
        delTrash()
        os.remove(audio)
