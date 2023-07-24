from flask import session, redirect, url_for
from werkzeug.security import check_password_hash

Users = [
    {
        "user":"prueba",
        "password":"pbkdf2:sha256:600000$ISFCZIBw42UqzXYk$2fc5091a44170014419aef48e4c55afa1e6ece06ec19f37894005deda8350c5a"
    }
]

def login_user(user,password):
    for item in Users:
        if item['user'] == user:
            if check_password_hash(item['password'],password):
                session['user'] = user
                return True
    return False

def login_required(func):
    def main_func(*args, **kwargs):
        if "user" in session:
            print(session['user'])
            return func(*args, **kwargs)
        else:
            return redirect(url_for("login"))
    main_func.__name__ = func.__name__
    return main_func
