import os
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_from_directory
from flask_socketio import SocketIO, emit, disconnect
from audio import delTrash, mergeAudios, saveAudio, saveMic
from user_manager import authenticated_only, login_user, login_required
from dotenv import load_dotenv
from whisper import resume, transcription, real_time, whisper_models
from werkzeug.utils import secure_filename, safe_join
load_dotenv()
import threading
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv('flask_secret_key') 
sock = SocketIO(app, cors_allowed_origins="*")
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
            carpet = f"./audio/final/{user}"
            if not os.path.exists(carpet):
                os.mkdir(carpet)
            return redirect(url_for("index"))
        flash("Usuario o contraseña inválido")
        return redirect(url_for('login'))
    return render_template("login.html")


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))




@app.route('/download/<filename>')
def downloadFile(filename):
    user = session['user']
    file = secure_filename(filename)
    audio_dir = f'./audio/final/{user}'
    return send_from_directory(audio_dir, file, as_attachment=True)



@app.route('/test', methods=["GET","POST"])
def test():
    if request.method == "POST":
        print(request)
        print(request.files)
    return render_template("tets.html")


@sock.on('testSock')
def testSock(buffer):
    print(type(buffer))


@sock.on("record")
@authenticated_only
def handle_record(data: bytes):
    sid = request.sid
    if sid not in record_chunks:
        record_chunks[sid] = []
    record_chunks[sid].append(data)


@sock.on("recordMic")
@authenticated_only
def handle_record_mic(data: bytes):
    sid = request.sid
    if sid not in mic_chunks:
        print("created")
        mic_chunks[sid] = []
    mic_chunks[sid].append(data)


@sock.on("message")
@authenticated_only
def handle_message(msg: str):
    print(msg)
    if msg == "stop":
        print("stopping")
        saveAudio(record_chunks) 
        saveMic(mic_chunks)
        mergeAudios()
        delTrash()
    if msg == "stopRealTime":
        session['realTime'].stop()
    


@sock.on("startTranscript")
@authenticated_only
def handle_model(data:dict):
    whisper_model = data['model']
    if whisper_model in whisper_models:
        audio = secure_filename(data['audio'])
        trans = threading.Thread(target=transcription, args=(whisper_model, audio, session['user'], request.sid, app))
        trans.start()

        

@sock.on("startChat")
@authenticated_only
def handle_chat(data:dict):
    resume(data['conversation'], data['question'])
    try:
        disconnect()
    except:
        pass

class RealTime():
    def __init__(self) -> None:
        self.running  = True

    def __bool__(self):
        return self.running
    
    def stop(self):
        self.running = False
    
    __nonzero__ = __bool__

@sock.on("startRealTime")
@authenticated_only
def handle_real_time():
    session['realTime'] = RealTime()
    trans = threading.Thread(target=real_time, args=(record_chunks,mic_chunks, request.sid, app, session['realTime']))
    trans.start()


@sock.on('disconnect')
def handle_disconnect():
    if 'realTime' in session:
        session['realTime'].stop()
    

if __name__ == "__main__":
    sock.run(
        app,
        "0.0.0.0",
        int(os.getenv("PORT", default=8000)),
        debug=os.getenv("DEBUG", default=False),
        use_reloader=False 
    )
