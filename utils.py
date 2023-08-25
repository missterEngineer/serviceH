import os
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
        path = f"{filepath}({cont}).{ext}"
        cont += 1
    return path
    
import re 
regex = re.compile(r'^[a-zA-Z0-9_]+$') 
def validate_string(string): 
    if regex.match(string): 
        return True 
    else: 
        return False 