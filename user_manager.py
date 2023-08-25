import functools
import json
from flask import session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from flask_socketio import disconnect


def get_users():
    with open("users.json", "r", encoding="utf-8") as file:
        users = json.loads(file.read())
    return users


def login_user(user,password):
    users = get_users()
    for item in users:
        if item['user'] == user:
            print("usuario existe")
            print(check_password_hash(item['password'], password))
            if check_password_hash(item['password'], password):
                session['user'] = user
                return True
    return False


def create_user(user:str, password:str):
    users = get_users()
    for item in users:
        if item['user'] == user or user == 'final':
            return {"error": "El usuario ya existe"}
    new_user = {
        "user":user,
        "password":generate_password_hash(password)
    }
    users.append(new_user)
    with open("users.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(users))
    return {"success":"success"}


def login_required(func):
    def main_func(*args, **kwargs):
        if "user" in session:
            return func(*args, **kwargs)
        else:
            return redirect(url_for("login"))
    main_func.__name__ = func.__name__
    return main_func


def authenticated_only(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        if not 'user' in session:
            disconnect()
        else:
            return func(*args, **kwargs)
    return wrapped
