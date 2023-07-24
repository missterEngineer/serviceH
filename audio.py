import subprocess
from pydub import AudioSegment
import time
from flask import session, request
import os


def saveAudio(record_chunks):
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
        subprocess.run(
            ["ffmpeg","-loglevel", "quiet", "-y", "-i",  video_path, "-f", "mp3", f"./audio/speaker{sid}.mp3"]
        )
        return True
    return False


def saveMic(mic_chunks):
    sid = request.sid
    mic_rec_chunks = mic_chunks[sid]
    if len(mic_rec_chunks) > 0:
        completeFile = mic_rec_chunks[0]
        for record in mic_rec_chunks:
            if record != completeFile:
                completeFile += record
        audio_path = f"./audio/mic{sid}.webm"
        file = open(audio_path, "wb")
        file.write(completeFile)
        file.close()
        mic_rec_chunks.clear()
        
        # Extract the audio using ffmpeg.
        subprocess.run(
            ["ffmpeg","-loglevel", "quiet", "-y", "-i",  audio_path, "-f", "mp3", f"./audio/mic{sid}.mp3"]
        )
 
        return True
    return False

def mergeAudios(realTime=False):
    sid = request.sid
    user = session['user']
    speaker_path = f"./audio/speaker{sid}.mp3"
    mic_path = f"./audio/mic{sid}.mp3"
    micSound = AudioSegment.from_file(mic_path)
    if os.path.isfile(speaker_path):
        speakerSound = AudioSegment.from_file(speaker_path)
        mixSound = speakerSound.overlay(micSound)
    else:
        mixSound = micSound
    currentTime = time.strftime("%Y-%m-%d-%H-%M-%S",time.localtime())
    if realTime:
        path = f"./audio"
    path = f"./audio/final/{user}"
    if not os.path.isdir(path):
        os.mkdir(path)
    full_path = f"{path}/{currentTime}.mp3"
    mixSound.export(full_path, format='mp3')
    return full_path


def delTrash():
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

