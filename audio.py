import subprocess
from pydub import AudioSegment
import time
from flask import session, request
import os
old_chunks = {}

def saveAudio(record_chunks, sid=None):
    print(sid)
    if sid is None:
        sid = request.sid
    rec_chunks = record_chunks[sid]
    if len(rec_chunks) > 0:
        completeFile = rec_chunks[0]
        for record in rec_chunks:
            if record != completeFile:
                completeFile += record
        video_path = f"./audio/video{sid}.webm"
        file = open(video_path, "wb")
        file.write(completeFile)
        file.close()
        rec_chunks.clear()
        # Extract the audio using ffmpeg.
        print("converting audio")
        try:
            os.remove(f"./audio/speaker{sid}.mp3")
        except: pass
        subprocess.run(
            ["ffmpeg","-loglevel", "quiet", "-y", "-i",  video_path, "-f", "mp3", f"./audio/speaker{sid}.mp3"]
        )
        return True
    return False


def saveMic(mic_chunks, sid=None):
    print(sid)
    if sid is None:
        sid = request.sid
    mic_rec_chunks = mic_chunks[sid]
    old_chunk = mic_rec_chunks[0]

    if len(mic_rec_chunks) > 0:
        completeFile = mic_rec_chunks[0]
        for record in mic_rec_chunks:
            if record != completeFile:
                completeFile += record
        audio_path = f"./audio/mic{sid}.webm"
        try:
            os.remove(audio_path)
        except:
            pass
        file = open(audio_path, "wb")
        file.write(completeFile)
        file.close()
        print(len(mic_rec_chunks))
        mic_rec_chunks.clear()
        mic_rec_chunks.append(old_chunk)
        print("converting mic")
        # Extract the audio using ffmpeg.
        try:
            os.remove(f"./audio/mic{sid}.mp3")
        except: pass
        
        subprocess.run(
            ["ffmpeg","-loglevel", "quiet", "-y", "-i",  audio_path, "-f", "mp3", f"./audio/mic{sid}.mp3"]
        )
 
        return True
    return False

def mergeAudios(realTime=False, sid=None):
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
            mixSound = speakerSound
    
    currentTime = time.strftime("%Y-%m-%d-%H-%M-%S",time.localtime())
    if realTime:
        path = f"./audio"
    else:
        user = session['user']
        path = f"./audio/final/{user}"
    if not os.path.isdir(path):
        os.mkdir(path)
    full_path = f"{path}/{currentTime}.mp3"
    mixSound.export(full_path, format='mp3')
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

