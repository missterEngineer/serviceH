from dataclasses import dataclass
import json
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from flask_socketio import emit
import openai
from flask import request, session
import time
from datetime import datetime
from audio import delTrash, mergeAudios, saveAudio, saveMic
import os

old_chunks = {}
from gradio_client import Client
client = Client("https://sanchit-gandhi-whisper-jax-diarization.hf.space/")

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
load_dotenv()


def check_prompt(text):
    for prompt in FORBIDDEN_PROMPTS:
        if prompt in text:
            return True
    return False


def transcribe(path, sid):
    openai.organization = os.getenv("OPENAI_ORG")
    openai.api_key = os.getenv("OPENAI_API_KEY")
    audio_file= open(path, "rb")
    print("init diarization")
    print("end diarization")
    transcript = openai.Audio.transcribe("whisper-1", audio_file, language="es")
    texto = transcript.text
    texto = ""
    print("init text")
    print("end text")
    emit('response', texto, to=sid, namespace="/")
    """segments, _ =  model.transcribe(path,"es")
    for segment in segments:
        if check_prompt(segment.text):
            continue
        txt =  segment.text
        emit('response', txt, to=sid, namespace="/")"""


def transcription(whisper_model, audio, user, sid, app):
    app.app_context().push()
    transcribe(f"./audio/final/{user}/{audio}", sid)
    emit("end", to=sid, namespace="/")


def resume(conversation, question):
    messages = []
    messages.append({"role": "user", "content": question})
    response = "¡Por supuesto! Por favor, proporciona la conversación"
    messages.append({"role": "assistant", "content": response})
    messages.append({"role":"user", "content": question + conversation})
    openai.organization = os.getenv("OPENAI_ORG")
    openai.api_key = os.getenv("OPENAI_API_KEY")
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages = messages,
        stream = True
    )
    final_response = ""
    for obj in completion:
        chunk = obj["choices"][0]
        if chunk["finish_reason"] != "stop":
            msg = chunk["delta"]["content"]
            final_response += msg
            emit('chatResponse', msg, to=request.sid)  
    emit('chatEnd', to=request.sid)
    return final_response


def saveResponse(audio_name:str, conversation:str, question:str, answer:str):
    user_dir = "prompts/" + session['user']
    if not os.path.isdir(user_dir):
        os.mkdir(user_dir)
    fullpath = os.path.join(user_dir, audio_name + ".json")
    if not os.path.isfile(fullpath):
        content = {
            "conversation": conversation,
            "messages" : [question, answer]
        }
    else:
        json_file = open(fullpath, "r", encoding="utf-8")
        content = json.loads(json_file.read())
        json_file.close()
        content["messages"].append(question)
        content["messages"].append(answer)
    json_data = json.dumps(content)
    json_file = open(fullpath, "w", encoding="utf-8")
    json_file.write(json_data)
    json_file.close()

        


def real_time(record_chunks, mic_chunks, sid, app, realTime):
    seconds = 0
    app.app_context().push()
    while realTime:
        if (seconds < 5):
            time.sleep(5 - seconds)
        saveAudio(record_chunks, sid)
        saveMic(mic_chunks, sid)
        audio = mergeAudios(True, sid)
        start_time = datetime.now()
        transcribe(audio, sid)
        final_time = datetime.now()
        seconds = (final_time - start_time).seconds
        print(seconds)
        os.remove(audio)
    #delTrash(sid)
