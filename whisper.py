import json
from dotenv import load_dotenv
from flask_socketio import emit
import openai
import os
from prompts import MessageGPT, send_to_GPT
from utils import  error_log, gladia
from pydub import AudioSegment
import uuid
import tiktoken
from flask import Flask, request
load_dotenv()
openai.organization = os.getenv("OPENAI_ORG")
openai.api_key = os.getenv("OPENAI_API_KEY")


def transcribe(path:str, sid:str, user:str, speaker:bool=False) -> None:   
    segments = divide_audio(path)
    print("init transcribe")
    final_text = ''
    for file_path in segments:
        
        if speaker:
            text = gladia(file_path)
        else:
            with open(file_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe("whisper-1", audio_file, language="es")
            text = transcript.text
        final_text += text
        emit('response', text, to=sid, namespace="/")
        if file_path != path:
            os.remove(file_path)
    audio_name = path.split("/")[-1]
    saveResponse(audio_name, final_text, user=user)
    print("end transcribe")


def divide_audio(path:str) -> list:
    MAX_BYTES = 24 * 1e+6 #24 megabytes (whisper api limit)
    size = os.path.getsize(path)
    if size < MAX_BYTES:
        return [path]
    segments = []
    MAX_MILLISECONDS = 20 * 60 * 1000 #20 min
    format = path.split(".")[-1]
    mp3 = AudioSegment.from_file(path, format)
    length = len(mp3)
    for f in range(int(length/MAX_MILLISECONDS)): 
        new_data = mp3[MAX_MILLISECONDS * f : MAX_MILLISECONDS * (f+1)]
        random_name = str(uuid.uuid1()).replace('-', '')
        new_path = f"./audio/tmp/{random_name}.mp3"
        new_data.export(new_path, format='mp3')
        segments.append(new_path)
        del new_data
    del mp3
    return segments


def transcription(model:str, audio:str, user:str, sid:str, app:Flask) -> None:
    app.app_context().push()
    path = f"./audio/final/{user}/{audio}"
    transcript_args = [path, sid, user]
    if model == "speaker":
        transcript_args.append(True)
    try:
        transcribe(*transcript_args)
    except Exception as e:
        emit('response', "Ha ocurrido un error al transcribir", to=sid, namespace="/")
        error_log(user, f"transcribe: {e}")
    emit("end", to=sid, namespace="/")


def resume(conversation:str, question:str) -> str:
    response = "¡Por supuesto! Por favor, proporciona la conversación"
    total_words = question + conversation + response
    tokens = num_tokens_from_string(total_words, "gpt-3.5-turbo")
    if tokens > 16000:
        emit('chatResponse', "La conversación es demasiada larga", to=request.sid) 
        return ''
    if tokens > 4000:
        model = "gpt-3.5-turbo-16k"
    else:
         model = "gpt-3.5-turbo"
    msg1 = MessageGPT("user", question).__dict__()
    msg2 = MessageGPT("assistant", response).__dict__()
    msg3 = MessageGPT("assistant", conversation).__dict__()
    messages = [msg1, msg2, msg3]
    final_response = send_to_GPT(messages, model)
    return final_response


def saveResponse(audio_name:str, conversation:str, question:str ='', answer:str ='', user:str='') -> None:
    user_dir = "prompts/" + user
    if not os.path.isdir(user_dir):  os.mkdir(user_dir)
    fullpath = os.path.join(user_dir, audio_name + ".json")
    content = {}
    if os.path.isfile(fullpath):
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
    

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens
