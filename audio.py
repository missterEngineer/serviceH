import subprocess
from pydub import AudioSegment
import time
from flask import session, request
import os
from utils import check_filename, error_log
from flask_socketio import emit
from werkzeug.utils import secure_filename


def saveAudio(record_chunks, sid=None):
    if sid is None:
        sid = request.sid
    video_path = f"./audio/video{sid}.webm"
    print("converting audio")
    try:
        os.remove(f"./audio/speaker{sid}.mp3")
    except: pass
    subprocess.run(
        ["ffmpeg", "-y", "-i",  video_path, "-f", "mp3", f"./audio/speaker{sid}.mp3"]
    )
    print("speaker saved")
    return True


def saveMic(mic_chunks, sid=None):
    print(sid)
    if sid is None:
        sid = request.sid
    audio_path = f"./audio/mic{sid}.webm"
    # Extract the audio using ffmpeg.
    print("converting mic")
    subprocess.run(
        ["ffmpeg", "-y", "-i",  audio_path, "-f", "mp3", f"./audio/mic{sid}.mp3"]
    )
    print("mic saved")
    return True

def mergeAudios(realTime=False, sid=None, filename="", user=""):
    print(sid)
    if sid is None:
        sid = request.sid
    
    speaker_path = f"./audio/speaker{sid}.mp3"
    mic_path = f"./audio/mic{sid}.mp3"
    if os.path.isfile(mic_path):
        micSound = AudioSegment.from_file(mic_path)
        mixSound = micSound
        if os.path.isfile(speaker_path):
            speakerSound = AudioSegment.from_file(speaker_path)
            mixSound = speakerSound.overlay(micSound)
        else:
            mixSound = micSound
    else:
        if os.path.isfile(speaker_path):
            speakerSound = AudioSegment.from_file(speaker_path)
            mixSound = speakerSound

            
    currentTime = time.strftime("%Y-%m-%d-%H-%M-%S",time.localtime())
    if realTime:
        path = f"./audio"
    else:
        path = f"./audio/final/{user}"
    if not os.path.isdir(path):
        os.mkdir(path)
    if not filename:
        filename = currentTime
    full_path = f"{path}/{filename}.mp3"
    full_path = check_filename(full_path)
    mixSound.export(full_path, format='mp3')
    print("audio saved")
    return full_path


def delTrash(sid=None):
    if sid is None:
        sid = request.sid
    trash_list =[
        f"./audio/video{sid}.webm",
        f"./audio/mic{sid}.webm",
        f"./audio/mic{sid}.mp3",
        f"./audio/speaker{sid}.mp3",
    ]
    for item in trash_list:
        if os.path.isfile(item):
            os.remove(item)

def save_record(record_name, sid, username, app, save_audio=True):
    app.app_context().push()
    try:
        if save_audio:
            saveAudio(None, sid) 
        saveMic(None, sid)
        mergeAudios(filename=record_name, sid=sid, user=username)
        delTrash(sid)
        emit('success_saving', to=sid, namespace="/")
    except Exception as e:
        error_log(username, f"save_record: {e}")
        emit('error_saving', to=sid, namespace="/")


def update_file_name(user:str, old_filename:str, new_filename:str) -> dict:
    old_filename = secure_filename(old_filename).replace(" ", "_")
    new_filename = secure_filename(new_filename).replace(" ", "_")
    audios_dir = f'./audio/final/{user}'
    filepath = os.path.join(audios_dir, old_filename)
    if not os.path.isfile(filepath):
        return {"status":400, "message":"Archivo no encontrado"}
    new_filepath = os.path.join(audios_dir, new_filename)
    if os.path.isfile(new_filepath):
        return {"status":400, "message":"Nombre de archivo ya existe"}
    if new_filename.split(".")[-1] != old_filename.split(".")[-1]:
        return {"status":400, "message":"Formato de archivo no valido"}
    os.rename(filepath, new_filepath)
    return {"status":200, "message":"Nombre de archivo actualizado"}