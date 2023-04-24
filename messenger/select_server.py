import select
from socket import socket, AF_INET, SOCK_STREAM
from wrapper_server_log import log
from log import server_log_config
import argparse
import sys
from datetime import datetime


logger = server_log_config.get_logger(__name__)


@log
def create_parser():
    try:
        parser = argparse.ArgumentParser(description='Start server')
        parser.add_argument ('-a', '--addr', default='', help='Server ip address, default localhost')
        parser.add_argument ('-p', '--port', default=7777, help='TCP - port on the server, default 7777')
        return parser
    except Exception as e:
        logger.critical(e)


@log
def read_requests(r_clients, all_clients):
    responses = {} 
    for sock in r_clients:
        try:
            data = sock.recv(1024).decode('utf-8')
            #data = eval(data)
            responses[sock] = data
        except:
            logger.info('Клиент {} {} отключился'.format(sock.fileno(), sock.getpeername()))
            all_clients.remove(sock)
        return responses
    
@log
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
                    "message": "Вы написали сообщение"
                    }
        else:
            msg = {
                "action": "probe",
                "time": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                }
            
        return msg
    except Exception as e:
        logger.error(e)
    
@log
def write_responses(requests, w_clients, all_clients):
    for sock in w_clients:
        if sock in requests:
            try:
                print(requests)
                for k, v in requests.items():
                    resp = v
                answer = resp
                print(answer)
                sock.send(str(answer).encode('utf-8'))
                logger.info(f'Клиенту отправлено сообщение {answer}')
            except: 
                logger.info('Клиент {} {} отключился'.format(sock.fileno(),
                sock.getpeername()))
                sock.close()
                all_clients.remove(sock)


def main(port, addr):

    logger.info(
        f'Запущен сервер, порт для подключений: {port}, '
        f'адрес с которого принимаются подключения: {addr}. ')

    address = (addr, port)
    clients = []
    s = socket(AF_INET, SOCK_STREAM)
    s.bind(address)
    s.listen(5)
    s.settimeout(0.2) 
    while True:
        try:
            conn, addr = s.accept() 
        except OSError as e:
            pass 
        else:
            logger.info("Получен запрос на соединение от %s" % str(addr))
            clients.append(conn)
        finally:
            wait = 10
            r = []
            w = []
            try:
                if clients:
                    r, w, e = select.select(clients, clients, [], wait)
            except OSError:
                pass 
            if r:
                requests = read_requests(r, clients)
                if requests:
                    for k, v in requests.items():
                        #print(v)
                        v = eval(v)
                        req = response_msg(v)
                        requests[k] = req       
                    write_responses(requests, w, clients) 
                        

if __name__ == "__main__":
    try:
        parser = create_parser()
        namespace = parser.parse_args(sys.argv[1:])
        port = namespace.port
        addr = namespace.addr
        main(port, addr)
    except Exception as e:
        logger.critical(e)
