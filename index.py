import subprocess
from flask import Flask,render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
sock = SocketIO(app)
record_chunks = []

@app.route("/")
def index():
    return render_template("index.html")

@sock.on('record')
def handdle_record(data:bytes):
    print(len(record_chunks))
    record_chunks.append(data)

@sock.on('message')
def handle_message(msg:str):
    if msg == "stop":
        print(len(record_chunks))
        completeFile = record_chunks[0]
        for record in record_chunks:
            if record != completeFile:
                completeFile += record
        file = open("video.webm","wb")
        file.write(completeFile)
        file.close()
        record_chunks.clear()
        # Extract the audio using ffmpeg.
        subprocess.run([
            "ffmpeg", "-i", "./video.webm", "-f", "mp3", "./audio" + ".mp3"
        ])


if __name__ == '__main__':
    sock.run(app,"0.0.0.0",debug=True,allow_unsafe_werkzeug=True)
