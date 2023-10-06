import json
import os
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for, send_from_directory
from flask_socketio import SocketIO
from audio import save_record, update_file_name
from prompts import answer_interview, append_prompt, remove_prompt, resend_msg, start_burnout, start_business, start_english, start_interview, start_interview_2, start_pray, update_prompt
from user_manager import admin_required, authenticated_only, create_user, login_user, login_required, change_password
from dotenv import load_dotenv
from whisper import resume, saveResponse,  transcription
from werkzeug.utils import secure_filename
from utils import allowed_file, check_filename, get_json_api, scan_audios, valid_audio_file, valid_mic_file, error_log
import threading

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv('flask_secret_key') 
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)
sock = SocketIO(app, cors_allowed_origins="*")


@app.route("/")
@login_required
def index():
    user = session['user']
    audios = scan_audios(user)
    return render_template("new_template/index.html", audios=audios)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["user"]
        password = request.form["password"]
        if login_user(user, password):
            return redirect(url_for("index"))
        flash("Usuario o contraseña inválido")
        return redirect(url_for('login'))
    return render_template("new_template/login.html")


@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route("/recorder")
@login_required
def recorder():
    return render_template("new_template/recorder.html")


@app.route('/create_user', methods=["GET","POST"])
@admin_required
def create_user_view():
    if request.method == "POST":
        user = request.form['user']
        password = request.form['password']
        return create_user(user, password)
    return render_template("new_template/add_user.html")


@app.route("/interview")
@login_required
def interview():
    return render_template("new_template/interview.html")


@app.route("/hutrit/list")
@login_required
def hutrit_list():
    api_link = "https://servidor-production.up.railway.app/hutritBack/public/getListTalents"
    talents = get_json_api(api_link)['listTalents']
    return render_template("new_template/hutrit_list.html", talents=talents)


@app.route("/hutrit/talent/<talent_id>")
@login_required
def hutrit_talent(talent_id):
    api_link = f"https://servidor-production.up.railway.app/hutritBack/public/getProfileProfessionalTalent?idTalent={talent_id}"
    talent = get_json_api(api_link)['talentInfo']
    skills_list = [skill['skills_categori']["skill"]["name"] for skill in talent['talen_skills']]
    skills = ", ".join(skills_list) 
    return render_template("new_template/hutrit_interview.html", talent=talent, skills=skills)


@app.route("/chat")
@login_required
def chat_test():
    return render_template("new_template/chat.html")


@sock.on('start_interview')
def start_interview_handler(values:dict):
    skills = values.get("skills")
    position = values.get("position")
    xp_years = values.get("xp_years")
    name = values.get("name")
    if name:
        start_interview_2(name, xp_years, skills)
    else:
        start_interview(position, xp_years, skills)


@sock.on('start_english')
@authenticated_only
def start_interview_handler(values:dict):
    level = values.get("level")
    start_english(level)


@sock.on('start_business')
@authenticated_only
def start_business_handler(values:dict):
    level = values.get("level")
    start_business(level)


@sock.on('start_burnout')
@authenticated_only
def start_burnout_handler():
    start_burnout()


@sock.on('start_pray')
def start_pray_handler():
    start_pray()


@app.route("/player/<audio>")
@login_required
def player_audio(audio:str):
    with open("prompts.json", "r", encoding="utf-8") as file:
        prompts = json.loads(file.read())
    context = {
        "prompts":prompts,
        "audio":audio
    }
    print(context)
    return render_template("new_template/transcript.html", **context)


@app.route('/download/<filename>')
@login_required
def downloadFile(filename):
    user = session['user']
    file = secure_filename(filename)
    audio_dir = f'./audio/final/{user}'
    return send_from_directory(audio_dir, file, as_attachment=True)


@app.route("/update_audio_name", methods=["POST"])
@login_required
def update_audio_name():
    old_filename = request.form["old"]
    new_filename = request.form["new"]
    user = session['user']
    return update_file_name(user, old_filename, new_filename)


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



@app.route('/upload_file', methods=["GET","POST"])
@login_required
def upload_file():
    if request.method == "POST":
        file = request.files.get('audio')
        if file is None : return abort(400)
        filename = file.filename
        if filename == "": return abort(400)
        if not allowed_file(filename): return abort(400)

        filename = secure_filename(file.filename)
        folder = f"audio/final/{session['user']}/"
        path = os.path.join(folder, filename)
        path = check_filename(path)
        file.save(path)
        return {"success":"success"}
    return render_template("upload_file.html")


@app.route("/recover_audio",methods=["POST"])
@login_required
def recover_audio():
    audio_file = request.files.get('audio_file')
    mic_file = request.files.get('mic_file')
    sid = request.form.get('sid')
    if valid_audio_file(audio_file.filename) and valid_mic_file(mic_file.filename):
        filename = ".".join(audio_file.filename.split(".")[0:-2])
        mic_path = f"./audio/mic{sid}.webm"
        mic_file.save(mic_path)
        audio_path = f"./audio/speaker{sid}.mp3"
        audio_file.save(audio_path)
        thread = threading.Thread(target=save_record, args=(filename, sid, session['user'], app, False))
        thread.start()
        return {"success":"success"}
    error_log(session['user'], f"recover_audio: not valid name '{audio_file.filename}' or '{mic_file.filename}'")
    return abort(400)


@app.route("/change_password", methods=["GET","POST"])
@login_required
def change_pass():
    if request.method == "POST":
        user = session['user']
        password = request.form.get("password")
        verify_password = request.form.get("verify_password")
        if password != verify_password:
            return {"response": "error", "msg":"Las contraseñas no coinciden"}
        change_password(user, password)
        return {"response":"success", "msg": "Contraseña cambiada exitosamente"}
    return render_template("new_template/change_password.html")


@app.route("/english")
@login_required
def english():
    return render_template("new_template/english.html")


@app.route("/pray")
def pray():
    return render_template("new_template/versiculo.html")


@app.route("/burnout")
@login_required
def burnout():
    return render_template("new_template/burnout.html")


@app.route("/business")
@login_required
def business():
    return render_template("new_template/business.html")


@app.route("/save_error", methods=["POST"])    
@login_required
def save_error():
    page = request.form.get("page")
    user = session['user']
    error = request.form.get("error")
    error_log(user, f"front-{page} {error}")
    return {'success':'success'}


@app.route("/save_prompt", methods=["POST"])    
@admin_required
def save_prompt():
    title = request.form.get("title")
    question = request.form.get("prompt")
    append_prompt(title, question)
    return {"success": "success"}


@app.route("/edit_prompt", methods=["POST"])    
@admin_required
def edit_prompt():
    title = request.form.get("title")
    prompt_id = request.form.get("id")
    update_prompt(title, prompt_id)
    return {"success": "success"}


@app.route("/del_prompt", methods=["POST"])    
@admin_required
def del_prompt():
    prompt_id = request.form.get("id")
    remove_prompt(prompt_id)
    return {"success": "success"}


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
    model = data['model']
    audio = secure_filename(data['audio'])
    trans = threading.Thread(target=transcription, args=(model, audio, session['user'], request.sid, app))
    trans.start()
        

@sock.on("startChat")
@authenticated_only
def handle_chat(data:dict):
    audio_name = data["audio_name"]
    conversation = data["conversation"]
    question = data["question"]
    answer = resume(conversation, question)
    user = session['user']
    if audio_name:
        saveResponse(audio_name, conversation, question, answer, user)      
    

@sock.on('answer_interview')
@authenticated_only
def answer_interview_handler(answer:str):
    answer_interview(answer)


@sock.on('chatTryAgain')
def chat_try_again_handler():
    resend_msg()


if __name__ == "__main__":
    sock.run(
        app,
        "0.0.0.0",
        int(os.getenv("PORT", default=8000)),
        debug=os.getenv("DEBUG", default=False),
        use_reloader=os.getenv("RELOAD", default=False) 
    )
    print("running")
