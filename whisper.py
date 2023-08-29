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
from utils import allowed_file, check_filename
from openai.error import RateLimitError, InvalidRequestError
old_chunks = {}
from gradio_client import Client
import time
from pydub import AudioSegment

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
    size = os.path.getsize(path)
    segments = []
    if size >= 24 * 1e+6: #Greater than 24 megabytes (whisper api limit)
        minutes = 20 * 60 * 1000
        mp3 = AudioSegment.from_mp3(path)
        length = len(mp3)
        for f in range(int(length/minutes)): 
            new_data = mp3[minutes*f:minutes*(f+1)]
            new_path = f"{path}.{f}.mp3"
            new_data.export(new_path,format='mp3')
            segments.append(new_path)
    else:
        segments.append(path)
    print("init diarization")
    try:
        for file_path in segments:
            audio_file= open(file_path, "rb")
            transcript = openai.Audio.transcribe("whisper-1", audio_file, language="es")
            texto = transcript.text
            emit('response', texto, to=sid, namespace="/")
            if file_path != path:
                os.remove(file_path)
            time.sleep(20)
    except Exception as e:
        print(e)
        emit('response', "Ha ocurrido un error al transcribir", to=sid, namespace="/")



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
    tokens = num_tokens_from_string((question*2) + conversation + response, "gpt-3.5-turbo")
    if tokens <= 4000:
        model = "gpt-3.5-turbo"
    elif tokens <= 16000:
        model = "gpt-3.5-turbo-16k"
    else:
        emit('chatResponse', "La conversación es demasiada larga", to=request.sid) 
        return
    final_response = ""
    print("prompt send")
    try:
        completion = openai.ChatCompletion.create(
            model=model,
            messages = messages,
            stream = True
        )
        for obj in completion:
            chunk = obj["choices"][0]
            if chunk["finish_reason"] != "stop":
                msg = chunk["delta"]["content"]
                final_response += msg
                emit('chatResponse', msg, to=request.sid)  
    except RateLimitError: 
        time.sleep(25)
        return resume(conversation, question)
    except Exception as e:
        print(e)
        emit('chatResponse', "Ha ocurrido un error, espere unos segundos e intente de nuevo", to=request.sid) 
    print("prompt received")
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

import tiktoken

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

