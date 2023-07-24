import subprocess
from pydub import AudioSegment
import time
from flask import session, request
import os


def saveAudio(record_chunks):
    if len(record_chunks) > 0:
        sid = request.sid
        rec_chunks = record_chunks[sid]
        completeFile = rec_chunks[0]
        for record in rec_chunks:
            if record != completeFile:
                completeFile += record
        video_path = f"./audio/video{sid}.webm"
        file = open(video_path, "wb")
        file.write(completeFile)
        file.close()
        
        # Extract the audio using ffmpeg.
        subprocess.run(
            ["ffmpeg","-loglevel", "quiet", "-y", "-i",  video_path, "-f", "mp3", f"./audio/speaker{sid}.mp3"]
        )
        os.remove(video_path)
        return True
    return False


def saveMic(mic_chunks):
    if len(mic_chunks) > 0:
        sid = request.sid
        rec_chunks = mic_chunks[sid]
        completeFile = rec_chunks[0]
        for record in rec_chunks:
            if record != completeFile:
                completeFile += record
        audio_path = f"./audio/mic{sid}.webm"
        file = open(audio_path, "wb")
        file.write(completeFile)
        file.close()
        # Extract the audio using ffmpeg.
        subprocess.run(
            ["ffmpeg","-loglevel", "quiet", "-y", "-i",  audio_path, "-f", "mp3", f"./audio/mic{sid}.mp3"]
        )
        os.remove(audio_path)
        return True
    return False

def mergeAudios():
    sid = request.sid
    user = session['user']
    speakerSound = AudioSegment.from_file(f"./audio/speaker{sid}.mp3")
    micSound = AudioSegment.from_file(f"./audio/mic{sid}.mp3")
    mixSound = speakerSound.overlay(micSound)
    currentTime = time.strftime("%Y-%m-%d-%H-%M-%S",time.localtime())
    path = f"./audio/final/{user}"
    if not os.path.isdir(path):
        os.mkdir(path)
    mixSound.export(f"{path}/{currentTime}.mp3", format='mp3')
