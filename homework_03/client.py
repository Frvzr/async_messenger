from socket import *
import sys
import argparse
from datetime import datetime


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-p', '--port', default=7777, help='TCP port for work, default 7777')
    parser.add_argument ('-a', '--addr', default='', help='Listening IP, default localhost')
    return parser

def authenticate():
    msg = {
            "action": "authenticate",
            "time": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            "user": {
                "account_name": "C0deMaver1ck",
                "password": "CorrectHorseBatterStaple"
            }
        }
    return msg

def response_msg(data):
    if 'response' in data:
        if data['response'] == 200:
            msg = {
                "action": "join",
                "time": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                "room": "#room_name"
                }
            
    elif 'action' in data:
            if data['action'] == "probe":
                msg = {
                    "action": "presence",
                    "time": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                    "type": "status",
                    "user": {
                    "account_name": "C0deMaver1ck",
                    "status": "Yep, I am here!"
                    }
                    }
            elif data['action'] == "msg":
                message = input("Введите ваше сообщение: ")
                msg = {
                    "action": "msg",
                    "time": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                    "to": "account_name",
                    "from": "account_name",
                    "encoding": "ascii",
                    "message": message
                    }
    else:
         msg = {
                "action": "quit"
                }
    return msg

def send_message(socket, server, msg):
    return socket.sendto(str(msg).encode('utf-8'), server)

def main(port, addr):
    s = socket(AF_INET, SOCK_DGRAM)
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    server = (addr, int(port))
    data = authenticate()
    send_message(s, server, data)
    while True:
        data, server = s.recvfrom(1024)
        print(data.decode('utf-8'))
        data = eval(data)
        msg = response_msg(data)
        if 'message' in msg and msg['message'] == "quit":
            send_message(s, server, msg)
            s.close()
            break
        else:
            send_message(s, server, msg)


if __name__ == "__main__":
    try:
        parser = create_parser()
        namespace = parser.parse_args(sys.argv[1:])
        port = namespace.port
        addr = namespace.addr
        main(port, addr)
    except Exception as e:
        print(e)
