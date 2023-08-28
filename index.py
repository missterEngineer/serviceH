import json
import os
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for, send_from_directory
from flask_socketio import SocketIO, emit, disconnect
from audio import delTrash, mergeAudios, save_record, saveAudio, saveMic
from user_manager import authenticated_only, create_user, login_user, login_required
from dotenv import load_dotenv
from whisper import resume, saveResponse, transcription, real_time, whisper_models
from werkzeug.utils import secure_filename, safe_join
from utils import allowed_file, check_filename

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
    print(session['user'])
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
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/download/<filename>')
@login_required
def downloadFile(filename):
    user = session['user']
    file = filename
    file = secure_filename(filename)
    print(file)
    audio_dir = f'./audio/final/{user}'
    return send_from_directory(audio_dir, file, as_attachment=True)



@app.route('/del_file')
@login_required
def del_file():
    filename = request.args.get("filename")
    if filename:
        user = session['user']
        filename = secure_filename(filename)
        full_path = os.path.join("audio/final/", f"{user}/", filename)
        if os.path.isfile(full_path):
            os.remove(full_path)
            return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
    abort(400)


@app.route('/get_prompts')
@login_required
def get_prompts():
    filename = request.args.get("filename")
    if filename:
        user = session['user']
        filename = secure_filename(filename)
        full_path = os.path.join("prompts/", f"{user}/", filename + ".json")
        if os.path.isfile(full_path):
            json_file = open(full_path, "r", encoding="utf-8")
            json_data = json_file.read()
            json_file.close()
            return json.dumps(json_data), 200, {'ContentType':'application/json'} 
    abort(400)


@app.route('/create_user', methods=["GET","POST"])
@login_required
def create_user_view():
    if request.method == "POST":
        user = request.form['user']
        password = request.form['password']
        return create_user(user, password)
    return render_template("create_user.html")


@app.route('/upload_file', methods=["GET","POST"])
@login_required
def upload_file():
    if request.method == "POST":
        file = request.files.get('audio')
        if file is None :
            print("is none")
            return abort(400)
        filename = file.filename
        if filename == "":
            print("is empty")
            return abort(400)
        if allowed_file(filename):
            filename = secure_filename(file.filename)
            folder = f"audio/final/{session['user']}/"
            path = os.path.join(folder, filename)
            path = check_filename(path)
            file.save(path)
            return {"success":"success"}
        print("is not valid")
        return abort(400)
    return render_template("upload_file.html")


@app.route("/recover_audio",methods=["POST"])
@login_required
def recover_audio():
    audio_file = request.files.get('audio_file')
    mic_file = request.files.get('mic_file')
    sid = request.form.get('sid')
    print(audio_file.filename, mic_file.filename)
    if valid_audio_file(audio_file.filename) and valid_mic_file(mic_file.filename):
        filename = ".".join(audio_file.filename.split(".")[0:-2])
        mic_path = f"./audio/mic{sid}.webm"
        mic_file.save(mic_path)
        audio_path = f"./audio/speaker{sid}.mp3"
        audio_file.save(audio_path)
        thread = threading.Thread(target=save_record, args=(filename, sid, session['user'], app, False))
        thread.start()
        return {"success":"success"}
    return abort(400)

    
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

    

@sock.on('testSock')
@authenticated_only
def testSock(buffer):
    print(type(buffer))


@sock.on("record")
@authenticated_only
def handle_record(data: bytes):
    sid = request.sid
    video_path = f"./audio/video{sid}.webm"
    file = open(video_path, "ab")
    file.write(data)
    file.close()


@sock.on("recordMic")
@authenticated_only
def handle_record_mic(data: bytes):
    sid = request.sid
    video_path = f"./audio/mic{sid}.webm"
    file = open(video_path, "ab")
    file.write(data)
    file.close()


@sock.on("message")
@authenticated_only
def handle_message(msg: str):
    if msg == "stopRealTime":
        session['realTime'].stop()
    

@sock.on("stopRecord")
@authenticated_only
def stop_record(record_name:str):
    print(record_name)
    print("stopping")
    record_name = secure_filename(record_name)
    thread = threading.Thread(target=save_record, args=(record_name, request.sid, session['user'], app))
    thread.start()



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
    audio_name = data["audio_name"]
    conversation = data["conversation"]
    question = data["question"]
    answer = resume(conversation, question)
    if audio_name:
        saveResponse(audio_name, conversation, question, answer)
        

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
        use_reloader=os.getenv("RELOAD", default=False) 
    )
    print("running")
