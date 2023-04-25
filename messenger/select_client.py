from socket import *
import os
import sys
curDir = os.getcwd()
sys.path.append(curDir)
from log import client_log_config
from wrapper_client_log import log
import argparse
import sys
from datetime import datetime


logger = client_log_config.get_logger(__name__)


@log
def create_parser():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument ('-p', '--port', default=7777, help='TCP port for work, default 7777')
        parser.add_argument ('-a', '--addr', default='localhost', help='Listening IP, default localhost')
        parser.add_argument('-m', '--mode', default='listen', nargs='?', help='Listen or send mode')
        return parser
    except Exception as e:
        logger.critical(e)



def main(port, addr, mode):

    logger.info(f'Запущен клиент с парамертами: адрес сервера: {addr}, порт: {port}')


    ADDRESS = (addr, port)
    with socket(AF_INET, SOCK_STREAM) as sock: 
        sock.connect(ADDRESS) 
        while True:
            if mode == 'send':
                message = input('Ваше сообщение: ')
                msg = {
                        "action": "msg",
                        "time": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                        "to": "account_name",
                        "from": "account_name",
                        "encoding": "ascii",
                        "message": message
                        }
                if msg == 'exit':
                    break
                sock.send(str(msg).encode('utf-8'))
                
            if mode == 'listen':
                data = sock.recv(1024).decode('utf-8')
                data = eval(data)
                answer = data['message']
                print('Ответ:', answer)


if __name__ == "__main__":
    try:
        parser = create_parser()
        namespace = parser.parse_args(sys.argv[1:])
        port = namespace.port
        addr = namespace.addr
        mode = namespace.mode
        main(port, addr, mode)
    except Exception as e:
        logger.critical(e)
