import select
import socket
from wrapper_server_log import log
from log import server_log_config
import argparse
import sys
import json

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
            responses[sock] = data
        except:
            logger.info('Клиент {} {} отключился'.format(sock.fileno(), sock.getpeername()))
            all_clients.remove(sock)
        return responses
    
    
@log
def get_message(client):
    encoded_response = client.recv(1024)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(encoding='utf-8')
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        else:
            raise 'Принято некорректное сообщение от удалённого компьютера.'
    else:
        raise 'Принято некорректное сообщение от удалённого компьютера.'
    
@log
def send_message(sock, message):
    js_message = json.dumps(message)
    encoded_message = js_message.encode(encoding='utf-8')
    sock.send(encoded_message)
    

@log
def process_message(message, names, listen_socks):
    if message['destination'] in names and names[message['destination']] in listen_socks:
        send_message(names[message['destination']], message)
        logger.info(f'Отправлено сообщение пользователю {message["destination"]} '
                    f'от пользователя {message["sender"]}.')
    elif message["destination"] in names and names[message["destination"]] not in listen_socks:
        raise ConnectionError
    else:
        logger.error(
            f'Пользователь {message["destination"]} не зарегистрирован на сервере, '
            f'отправка сообщения невозможна.')
    
    
@log
def process_client_message(message, messages_list, client, clients, names):
    logger.debug(f'Разбор сообщения от клиента : {message}')
    if 'action' in message and message['action'] == 'presence' and \
            'time' in message and 'user' in message:
        if message['user']['account_name'] not in names.keys():
            names[message['user']['account_name']] = client
            response = {'response': 200}
            send_message(client, response)
        else:
            response = {
                'response': 400,
                'error': 'Имя пользователя уже занято.'
            }
            send_message(client, response)
            clients.remove(client)
            client.close()
        return

    elif 'action' in message and message['action'] == 'message' and \
            'destination' in message and 'time' in message \
            and 'sender' in message and 'text' in message:
        messages_list.append(message)
        return

    elif 'action' in message and message['action'] == 'exit' and 'account_name' in message:
        clients.remove(names[message['account_name']])
        names[message['account_name']].close()
        del names[message['account_name']]
        return

    else:
        response = {
            'response': 400,
            'error': None
        }
        response['error'] = 'Запрос некорректен.'
        send_message(client, response)
        return
    
@log
def write_responses(requests, w_clients, all_clients):
    print(requests)
    for sock in w_clients:
        if sock in requests:
            try:
                answer = requests[sock]
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
        f'адрес с которого принимаются подключения: {addr}. '
        f'Если адрес не указан, принимаются соединения с любых адресов.')
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((addr, port))
    s.settimeout(1)


    clients = []
    messages = []

    names = dict()

    s.listen(5)

    while True:
        try:
            client, client_address = s.accept()
        except OSError:
            pass
        else:
            logger.info(f'Установлено соедение с ПК {client_address}')
            clients.append(client)

        recv_data_lst = []
        send_data_lst = []
        err_lst = []

        try:
            if clients:
                recv_data_lst, send_data_lst, err_lst = select.select(clients, clients, [], 0)
        except OSError:
            pass

        if recv_data_lst:
            for client_with_message in recv_data_lst:
                try:
                    process_client_message(get_message(client_with_message),
                                           messages, client_with_message, clients, names)
                except Exception:
                    logger.info(f'Клиент {client_with_message.getpeername()} '
                                f'отключился от сервера.')
                    clients.remove(client_with_message)


        for i in messages:
            try:
                process_message(i, names, send_data_lst)
            except Exception:
                logger.info(f'Связь с клиентом с именем {i["destinations"]} была потеряна')
                clients.remove(names[i['destination']])
                del names[i['destination']]
        messages.clear()

if __name__ == "__main__":
    try:
        parser = create_parser()
        namespace = parser.parse_args(sys.argv[1:])
        port = namespace.port
        addr = namespace.addr
        main(port, addr)
    except Exception as e:
        logger.critical(e)
