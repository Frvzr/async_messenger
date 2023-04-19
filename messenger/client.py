from socket import *
import sys
import argparse
from datetime import datetime
from log import client_log_config
from wrapper_log import log 


logger = client_log_config.get_logger(__name__)

@log
def create_parser():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument ('-p', '--port', default=7777, help='TCP port for work, default 7777')
        parser.add_argument ('-a', '--addr', default='localhost', help='Listening IP, default localhost')
        return parser
    except Exception as e:
        logger.critical(e)

@log
def authenticate():
    try:
        msg = {
                "action": "authenticate",
                "time": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                "user": {
                    "account_name": "C0deMaver1ck",
                    "password": "CorrectHorseBatterStaple"
                }
            }
        return msg
    except Exception as e:
        logger.error(e)

@log
def response_msg(data):
    try:
        if 'response' in data:
            if data['response'] == 200:
                logger.info(f"Authentication was successful")
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
        return msg
    except Exception as e:
        logger.error(e)

@log
def send_message(socket, server, msg):
    try:
        return socket.sendto(str(msg).encode('utf-8'), server)
    except Exception as e:
        logger.error(e)

def main(port, addr):
    try:
        logger.info(f"Connect to server {addr}")

        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        server = (addr, int(port))
        logger.info(f"Connection to {addr} was successful")
        data = authenticate()
        send_message(s, server, data)
        while True:
            data, server = s.recvfrom(1024)
            logger.info(f"Message send was successful")
            print(data.decode('utf-8'))
            data = eval(data)
            msg = response_msg(data)
            if ('message' in msg and msg['message'] == "quit") or msg['action'] == 'quit':
                s.close()
                break
            else:
                send_message(s, server, msg)
    except Exception as e:
        logger.critical(e)


if __name__ == "__main__":
    try:
        parser = create_parser()
        namespace = parser.parse_args(sys.argv[1:])
        port = namespace.port
        addr = namespace.addr
        main(port, addr)
    except Exception as e:
        logger.critical(e)