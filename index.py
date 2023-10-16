import os
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO
from prompts import answer_interview,  resend_msg, start_burnout, start_business, start_cybersecurity, start_english, start_interview, start_interview_2, start_pray, update_prompt
from dotenv import load_dotenv
from whisper import resume, saveResponse
from utils import get_json_api, error_log


load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv('flask_secret_key') 
"""app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)"""
sock = SocketIO(app, cors_allowed_origins="*")


@app.route("/")
def index():
    return render_template("new_template/index.html")


@app.route("/interview")
def interview():
    return render_template("new_template/interview.html")


@app.route("/hutrit/list")
def hutrit_list():
    api_link = "https://servidor-production.up.railway.app/hutritBack/public/getListTalents"
    talents = get_json_api(api_link)['listTalents']
    return render_template("new_template/hutrit_list.html", talents=talents)


@app.route("/hutrit/talent/<talent_id>")
def hutrit_talent(talent_id):
    api_link = f"https://servidor-production.up.railway.app/hutritBack/public/getProfileProfessionalTalent?idTalent={talent_id}"
    talent = get_json_api(api_link)['talentInfo']
    skills_list = [skill['skills_categori']["skill"]["name"] for skill in talent['talen_skills']]
    skills = ", ".join(skills_list) 
    return render_template("new_template/hutrit_interview.html", talent=talent, skills=skills)


@app.route("/chat")
def chat_test():
    return render_template("new_template/chat.html")


@sock.on('check_answers')
def check_answers_handler(values:dict):
    print(values)


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
def start_interview_handler(values:dict):
    level = values.get("level")
    start_english(level)


@sock.on('start_business')
def start_business_handler(values:dict):
    level = values.get("level")
    start_business(level)


@sock.on('start_burnout')
def start_burnout_handler():
    start_burnout()



@sock.on('start_pray')
def start_pray_handler():
    start_pray()


@sock.on('start_cybersecurity')
def start_cybersecurity_handler():
    start_cybersecurity()



@app.route("/english")
def english():
    return render_template("new_template/english.html")


@app.route("/cybersecurity")
def cybersecurity():
    return render_template("new_template/cybersecurity.html")


@app.route("/pray")
def pray():
    return render_template("new_template/versiculo.html")


@app.route("/burnout")
def burnout():
    return render_template("new_template/burnout.html")


@app.route("/business")
def business():
    return render_template("new_template/business.html")


@app.route("/save_error", methods=["POST"])    
def save_error():
    page = request.form.get("page")
    user = session['user']
    error = request.form.get("error")
    error_log(user, f"front-{page} {error}")
    return {'success':'success'}



@sock.on("startChat")
def handle_chat(data:dict):
    audio_name = data["audio_name"]
    conversation = data["conversation"]
    question = data["question"]
    answer = resume(conversation, question)
    user = session['user']
    if audio_name:
        saveResponse(audio_name, conversation, question, answer, user)      
    

@sock.on('answer_interview')
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
