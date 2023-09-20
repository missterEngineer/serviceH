import json
from dotenv import load_dotenv
from flask_socketio import emit
import openai
from flask import request, session
import time
from datetime import datetime
from audio import mergeAudios, saveAudio, saveMic
import os
from utils import  error_log, gladia
from openai.error import RateLimitError
old_chunks = {}
from gradio_client import Client
import time
from pydub import AudioSegment
import uuid

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


def transcribe(path:str, sid:str, user:str, speaker:bool=False):
    openai.organization = os.getenv("OPENAI_ORG")
    openai.api_key = os.getenv("OPENAI_API_KEY")
    size = os.path.getsize(path)
    segments = []
    if size >= 24 * 1e+6: #Greater than 24 megabytes (whisper api limit)
        minutes = 20 * 60 * 1000
        format = path.split(".")[-1]
        mp3 = AudioSegment.from_file(path, format)
        length = len(mp3)
        for f in range(int(length/minutes)): 
            new_data = mp3[minutes * f : minutes * (f+1)]
            random_name = str(uuid.uuid1()).replace('-', '')
            new_path = f"./audio/tmp/{random_name}.mp3"
            new_data.export(new_path, format='mp3')
            segments.append(new_path)
            del new_data
        del mp3
    else:
        segments.append(path)
    print("init transcribe")
    final_text = ''
    for file_path in segments:
        audio_file= open(file_path, "rb")
        if speaker:
            texto = gladia(file_path)
        else:
            transcript = openai.Audio.transcribe("whisper-1", audio_file, language="es")
            texto = transcript.text
        final_text += texto
        emit('response', texto, to=sid, namespace="/")
        if file_path != path:
            os.remove(file_path)
        if file_path != segments[-1]:
            time.sleep(20)
    audio_name = path.split("/")[-1]
    saveResponse(audio_name, final_text, user=user)
    print("end transcribe")


def speaker_detect(audio_file_path):
    return client.predict(
        audio_file_path,	# str (filepath or URL to file) in 'audio_path' Audio component
        "transcribe",	# str in 'Task' Radio component
        True,	# bool in 'Group by speaker' Checkbox component
        api_name="/predict"
    )



def transcription(model, audio, user, sid, app):
    app.app_context().push()
    try:
        transcript_args = [f"./audio/final/{user}/{audio}", sid, user]
        if model == "speaker":
            transcript_args.append(True)
        transcribe(*transcript_args)
    except Exception as e:
        print(e)
        emit('response', "Ha ocurrido un error al transcribir", to=sid, namespace="/")
        error_log(user,f"transcribe: {e}")
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
        error_log(session['user'], f"resume: {e}") 
    print("prompt received")
    emit('chatEnd', to=request.sid)
    return final_response


def saveResponse(audio_name:str, conversation:str, question:str ='', answer:str ='', user=''):
    if user == '':
        user = session['user']
    user_dir = "prompts/" + user
    if not os.path.isdir(user_dir):
        os.mkdir(user_dir)
    fullpath = os.path.join(user_dir, audio_name + ".json")
    if not os.path.isfile(fullpath):
        content = {
            "conversation": conversation,
            "messages":[]
        }
        if question and answer:
            content['messages'] = [question, answer]
    else:
        with open(fullpath, "r", encoding="utf-8") as json_file:
            json_file = open(fullpath, "r", encoding="utf-8")
            content = json.loads(json_file.read())
            content['conversation'] = conversation
            if question and answer:
                if not "messages" in content:
                    content["messages"] = []
                content["messages"].append(question)
                content["messages"].append(answer)
    json_data = json.dumps(content)
    with open(fullpath, "w", encoding="utf-8") as json_file:
        json_file.write(json_data)


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

