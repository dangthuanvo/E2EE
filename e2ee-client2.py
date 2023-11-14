import socket
import threading
from time import sleep
import requests
import rsa
import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO

app = Flask(__name__)
app.config["SECRET_KEY"] = "e2ee123"
PORT = 9999
server_ip = "192.168.1.16"
socketio = SocketIO(app)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
public_key, private_key = rsa.newkeys(1024)
tamper_public_key, tamper_private_key = rsa.newkeys(1024)
print(public_key)
print(private_key)
public_partner = None
myname = None


def connect_to_host():
    client.connect((server_ip, PORT))
    client.send(public_key.save_pkcs1(format='PEM'))
    client.send(myname.encode())

def receiving_messages():
    global client, public_partner, private_key
    while True:
        if(public_partner == None):
            public_partner = rsa.PublicKey.load_pkcs1(client.recv(1024))
        else:
            received_data = client.recv(1024)
            try:
                message = received_data.decode()
            except:
                messagensign = rsa.decrypt(received_data, private_key).decode()
                messagensignformat = messagensign.split('**')
                message = messagensignformat[0]
                sign = messagensignformat[1]
                try:
                    rsa.verify(message.encode(), sign, public_partner)
                except:
                    socketio.emit("message", {"name": 'CẢNH BÁO', "message": 'ĐOẠN CHAT CỦA BẠN ĐANG BỊ XÂM NHẬP'})
                    break
            messageformat = message.split(":")
            socketio.emit("message", {"name": messageformat[0], "message": messageformat[1]})




def sending_messages(message):
    global client, public_partner, myname
    message_to_send = f"{myname}: {message}"
    encrypted_message = rsa.encrypt(message_to_send.encode(), public_partner)
    sign = rsa.sign(message_to_send.encode(), private_key, 'SHA-1')
    if("mật khẩu" in message):
        client.send({encrypted_message}**{sign})  
    else:
        client.send(f"{myname}: {message}".encode())


@app.route("/", methods = ["POST", "GET"])
def index():
    global client, myname
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            return render_template("index.html", error="Please enter a name.", name=name)
        

        myname = name
        connect_to_host()
        #socketio.start_background_task(target=receiving_messages)
        receivie_thread = threading.Thread(target=receiving_messages, args=())
        receivie_thread.start()
        #send_thread = threading.Thread(target=sending_messages, args=()).start()
        # eventlet.spawn(receiving_messages())
        data = {
            'name': myname,
            'ip': server_ip
        }
        return render_template("room2.html", data=data, code=None)
    return render_template("index.html")

@socketio.on('message')
def handle_message(data):
    sending_messages(data["message"])
    message = data["message"]
    socketio.emit("message", {"name": myname, "message": message})

if __name__ == "__main__":
    socketio.run(app,port = 5001, debug=True)
    # socketio.start_background_task(target=receiving_messages)
