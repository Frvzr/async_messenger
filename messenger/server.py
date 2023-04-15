from socket import *
import sys
import argparse
from datetime import datetime
from log import server_log_config


logger = server_log_config.get_logger(__name__)


def create_parser():
    try:
        parser = argparse.ArgumentParser(description='Start server')
        parser.add_argument ('-a', '--addr', default='', help='Server ip address, default localhost')
        parser.add_argument ('-p', '--port', default=7777, help='TCP - port on the server, default 7777')
        return parser
    except Exception as e:
        logger.critical(e)


def response_msg(data):
    try:
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
    except Exception as e:
        logger.error(e)


def send_message(socket, msg, address):
    try:
        return socket.sendto(str(msg).encode('utf-8'), address)
    except Exception as e:
        logger.error(e)


def main(port, addr):
    try:
        logger.info("Start server")
        logger.warning("Test message")
        
        s = socket(AF_INET, SOCK_DGRAM) 
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) 
        s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1) 
        s.bind((addr, int(port)))
        while True:
            data, address = s.recvfrom(1024)
            print(data.decode('utf-8'))
            data = eval(data)
            msg = response_msg(data)
            send_message(s, msg, address)
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
