from flask import Flask,render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
sock = SocketIO(app)


@app.route("/")
def index():
    return render_template("index.html")

@sock.on('message')
def handle_message(data):
    print('received message: ' + data)

if __name__ == '__main__':
    sock.run(app,debug=True)