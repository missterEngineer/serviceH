import os
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_from_directory
from flask_socketio import SocketIO, emit
from audio import delTrash, mergeAudios, saveAudio, saveMic
from user_manager import login_user, login_required
from dotenv import load_dotenv
from whisper import resume, transcription, real_time, whisper_models
from werkzeug.utils import secure_filename
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv('flask_secret_key') 
sock = SocketIO(app)
record_chunks = {}
mic_chunks = {}


@app.route("/")
@login_required
def index():
    return render_template("menu.html")


@app.route("/recorder")
@login_required
def recorder():
    return render_template("recorder.html")


@app.route("/player")
@login_required
def player():
    user = session['user']
    audios = os.listdir(f'./audio/final/{user}')
    context={
        "whisper_models":whisper_models,
        "audios":audios
    }
    return render_template("player.html",**context)


@app.route("/transcript")
@login_required
def transcript():
    context={
        "whisper_models":whisper_models
    }
    return render_template("transcript.html", **context)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["user"]
        password = request.form["password"]
        if login_user(user, password):
            return redirect(url_for("index"))
        flash("Usuario o contraseña inválido")
        return redirect(url_for('login'))
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@sock.on("record")
@login_required
def handle_record(data: bytes):
    sid = request.sid
    if sid not in record_chunks:
        record_chunks[sid] = []
    record_chunks[sid].append(data)


@sock.on("recordMic")
@login_required
def handle_record_mic(data: bytes):
    sid = request.sid
    if sid not in mic_chunks:
        mic_chunks[sid] = []
    mic_chunks[sid].append(data)


@sock.on("message")
@login_required
def handle_message(msg: str):
    if msg == "stop":
        if saveAudio(record_chunks) and saveMic(mic_chunks):
            mergeAudios()
            delTrash()
    if msg == "stopRealTime":
        session['realTime'] = False


@sock.on("startTranscript")
@login_required
def handle_model(data:dict):
    whisper_model = data['model']
    if whisper_model in whisper_models:
        audio = secure_filename(data['audio'])
        transcription(whisper_model, audio)
        

@sock.on("startChat")
@login_required
def handle_chat(data:dict):
    resume(data['conversation'], data['question'])


@sock.on("startRealTime")
@login_required
def handle_real_time():
    session['realTime'] = True
    real_time(record_chunks, mic_chunks)


@sock.on('disconnect')
def handle_disconnect():
    session['realTime'] = False



if __name__ == "__main__":
    sock.run(
        app,
        "0.0.0.0",
        os.getenv("PORT", default=5000),
        debug=True,
        allow_unsafe_werkzeug=True,
    )
