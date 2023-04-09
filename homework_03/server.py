from socket import *
import sys
import argparse
from datetime import datetime



def create_parser():
    parser = argparse.ArgumentParser(description='Start server')
    parser.add_argument ('-a', '--addr', default='', help='Server ip address, default localhost')
    parser.add_argument ('-p', '--port', default=7777, help='TCP - port on the server, default 7777')
    return parser

def response_msg(data):
    if data['action'] == 'authenticate':
        if data['user']['account_name'] and data['user']['password']:
            msg = {
                "response": 200,
                "alert":"Все ок"
                }
        else:
            msg = {
                "response": 402,
                "error": 'This could be "wrong password" or "no account with that name"'
                }
    elif data['action'] == "join":
            msg = {
        "action": "msg",
        "time": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
        "room": "#room_name",
        "message": "Вы подключились к чату"
        }

    elif data['action'] == "msg":
        msg = { 
                "action": "msg",
                "time": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                "alert": "Вы написали сообщение"
                }

    else:
        msg = {
            "action": "probe",
            "time": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            }
        
    return msg
                
def send_message(socket, msg, address):
    return socket.sendto(str(msg).encode('utf-8'), address)

def main(port, addr):
    s = socket(AF_INET, SOCK_DGRAM) 
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) 
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1) 
    s.bind((addr, int(port)))
    while True:
        data, address = s.recvfrom(1024)
        print(data.decode('utf-8'))
        data = eval(data)
        if data['action'] == 'quit':
             s.close()
             break
        if 'message' in data:
            if data['message'] == "quit":
                s.close()
                break
            else:
                msg = response_msg(data)
                send_message(s, msg, address)  
        else:
            msg = response_msg(data)
            send_message(s, msg, address)


if __name__ == "__main__":
    try:
        parser = create_parser()
        namespace = parser.parse_args(sys.argv[1:])
        port = namespace.port
        addr = namespace.addr
        main(port, addr)
    except Exception as e:
        print(e)
