import subprocess


def saveAudio(record_chunks):
    if len(record_chunks) > 0:
        completeFile = record_chunks[0]
        for record in record_chunks:
            if record != completeFile:
                completeFile += record
        file = open("./audio/video.webm", "wb")
        file.write(completeFile)
        file.close()
        
        # Extract the audio using ffmpeg.
        subprocess.run(
            ["ffmpeg","-loglevel", "quiet", "-y", "-i",  "./audio/video.webm", "-f", "mp3", "./audio/speaker" + ".mp3"]
        )
        return True
    return False


def saveMic(mic_chunks):
    if len(mic_chunks) > 0:
        completeFile = mic_chunks[0]
        for record in mic_chunks:
            if record != completeFile:
                completeFile += record
        file = open("./audio/mic.webm", "wb")
        file.write(completeFile)
        file.close()
        # Extract the audio using ffmpeg.
        subprocess.run(
            ["ffmpeg","-loglevel", "quiet", "-y", "-i",  "./audio/mic.webm", "-f", "mp3", "./audio/mic" + ".mp3"]
        )
        return True
    return False

