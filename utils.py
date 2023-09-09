import os
from datetime import datetime
audio_formats = ['MP3', 'WAV', 'AAC', 'FLAC', 'OGG', 'WMA', 'ALAC', 'AIFF', 'M4A', 'AC3']


def allowed_file(filename):
    print(filename.rsplit('.', 1)[1].upper())
    return '.' in filename and \
           filename.rsplit('.', 1)[1].upper() in audio_formats


def check_filename(path:str):
    cont = 2
    file_parts = path.split(".")
    ext = file_parts.pop()
    filepath = ".".join(file_parts)
    while(os.path.isfile(path)):
        path = f"{filepath}_{cont}.{ext}"
        cont += 1
    return path
    

import re 
regex = re.compile(r'^[a-zA-Z0-9_]+$') 
def validate_string(string): 
    if regex.match(string): 
        return True 
    else: 
        return False 
    
def valid_audio_file(filename:str):
    splits = filename.split(".")
    if (splits[-1] == "mp3" and  splits[-2] == "computer"):
        return True
    return False


def valid_mic_file(filename:str):
    splits = filename.split(".")
    if (splits[-1] == "webm" and  splits[-2] == "mic"):
        return True
    return False


def error_log(user, reason):
    with open("errors.txt","a") as file:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log = f"{date} {user} {reason}\n"
        file.write(log)


def scan_audios(user:str)->dict:
    audios = []
    with os.scandir(f'./audio/final/{user}') as folder_items:
        for item in folder_items:
            if item.is_file():
                file_date_float = os.path.getmtime(item.path)
                file_date = datetime.fromtimestamp(file_date_float)
                audios.append({
                    "name": item.name,
                    "date": file_date.strftime('%m/%d/%Y')
                })
    return audios