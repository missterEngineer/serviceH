import os
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO
from audio import saveAudio, saveMic
from user_manager import login_user, login_required
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv('flask_secret_key') 
sock = SocketIO(app)
record_chunks = []
mic_chunks = []


@login_required
@app.route("/")
def index():
    return render_template("menu.html")

@login_required
@app.route("/recorder")
def recorder():
    return render_template("recorder.html")


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

@login_required
@sock.on("record")
def handle_record(data: bytes):
    record_chunks.append(data)

@login_required
@sock.on("recordMic")
def handle_record(data: bytes):
    mic_chunks.append(data)


@login_required
@sock.on("message")
def handle_message(msg: str):
    if msg == "stop":
        if saveAudio(record_chunks) and saveMic(mic_chunks):
            record_chunks.clear()
            mic_chunks.clear()



if __name__ == "__main__":
    sock.run(
        app,
        "0.0.0.0",
        os.getenv("PORT", default=5000),
        debug=True,
        allow_unsafe_werkzeug=True,
    )
