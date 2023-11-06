import json
import socket
import threading
import rsa
import requests
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
clientcount = 0
client1 = None
client2 = None
client1_name = None
client1_key = None
client2_name = None
client2_key = None
message_count = 0

def handle_message(client_socket):
    global message_count, client1, client2
    while True:
        if(message_count == 4):
            try:    
                message = client_socket.recv(1024)
                # int_val = int.from_bytes(message, "big")
                try:
                    print(f"{message.decode()} received from client")
                except:
                    print(f"{message} received from client")
                if not message:
                    break
                if(client_socket == client1):
                    client2.send(message)
                else:
                    client1.send(message)
            except Exception as e:
                print(f"Error: {str(e)}")
                break


def handle_connect(client_socket):
    global clientcount, client1_name, client1_key, client2_name, client2_key, client1, client2, message_count, client1, client2
    if(clientcount == 0):
        clientcount += 1
        client1 = client_socket
        client1_key = rsa.PublicKey.load_pkcs1(client_socket.recv(1024))
        client1_name = client_socket.recv(1024).decode()
    else:
        client2 = client_socket
        client2_key = rsa.PublicKey.load_pkcs1(client_socket.recv(1024))
        client2_name = client_socket.recv(1024).decode()
        client_message1 = threading.Thread(target=handle_message, args=(client1,)).start()
        client_message2 = threading.Thread(target=handle_message, args=(client2,)).start()
        client1.send(client2_key.save_pkcs1(format='PEM'))
        client2.send(client1_key.save_pkcs1(format='PEM'))
    message_count += 2

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((get_ip(), 9999))
server.listen()

print("Your IPv4 address is:", get_ip())
while True:
    client_socket, client_addr = server.accept()
    print(f"Accepted connection from {client_addr[0]}:{client_addr[1]}")
    # Create a new thread to handle the client
    client_connect = threading.Thread(target=handle_connect, args=(client_socket,))
    client_connect.start()


