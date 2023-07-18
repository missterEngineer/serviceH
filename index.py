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
    print("recording...")
    record_chunks.append(data)

@sock.on('message')
def handle_message(msg:str):
    if msg == "stop":
        completeFile = record_chunks[0]
        for record in record_chunks:
            if record != completeFile:
                completeFile += record
        file = open("video.webm","wb")
        file.write(completeFile)
        file.close()
        record_chunks = []


if __name__ == '__main__':
    sock.run(app,debug=True,allow_unsafe_werkzeug=True)