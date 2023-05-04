import socket
import os
import sys
curDir = os.getcwd()
sys.path.append(curDir)
from log import client_log_config
from wrapper_client_log import log
import argparse
import sys
from datetime import datetime
import json
import threading
import time


logger = client_log_config.get_logger(__name__)


@log
def create_parser():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument ('-p', '--port', default=7777, help='TCP port for work, default 7777')
        parser.add_argument ('-a', '--addr', default='localhost', help='Listening IP, default localhost')
        parser.add_argument('-n', '--name', default=None, nargs='?')
        return parser
    except Exception as e:
        logger.critical(e)
        

@log
def create_exit_message(account_name):
    return {
        'action': 'exit',
        'time': time.time(),
        'account_name': account_name
    }


@log
def message_from_server(sock, my_username):
    while True:
        try:
            message = get_message(sock)
            print(message)
            if 'action' in message and message['action'] == 'message' and \
                    'sender' in message and 'destination' in message \
                    and 'text' in message and message['destination'] == my_username:
                print(f'\nПолучено сообщение от пользователя {message["sender"]}:'
                      f'\n{message["text"]}')
                logger.info(f'Получено сообщение от пользователя {message["sender"]}:'
                            f'\n{message["text"]}')
            else:
                logger.error(f'Получено некорректное сообщение с сервера: {message}')
        except Exception:
            logger.error(f'Не удалось декодировать полученное сообщение.')
        # except:
        #     logger.critical(f'Потеряно соединение с сервером.')
        #     break


def print_help():
    """Функция выводящяя справку по использованию"""
    print('Поддерживаемые команды:')
    print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
    print('help - вывести подсказки по командам')
    print('exit - выход из программы')


@log
def create_message(sock, account_name='Guest'):
    to_user = input('Введите получателя сообщения: ')
    message = input('Введите сообщение для отправки: ')
    message_dict = {
        'action': 'message',
        'sender': account_name,
        'destination': to_user,
        'time': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
        'text': message
    }
    logger.debug(f'Сформирован словарь сообщения: {message_dict}')
    try:
        send_message(sock, message_dict)
        logger.info(f'Отправлено сообщение для пользователя {to_user}')
    except:
        logger.critical('Потеряно соединение с сервером.')
        sys.exit(1)

@log
def user_interactive(sock, username):
    print_help()
    while True:
        command = input('Введите команду: ')
        if command == 'message':
            create_message(sock, username)
        elif command == 'help':
            print_help()
        elif command == 'exit':
            send_message(sock, create_exit_message(username))
            print('Завершение соединения.')
            logger.info('Завершение работы по команде пользователя.')
            time.sleep(0.5)
            break
        else:
            print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')


@log
def get_message(client):
    encoded_response = client.recv(1024)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(encoding='utf-8')
        response = eval(json_response)
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
def create_presence(account_name):
    out = {
        'action': 'presence',
        'time': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
        'user': {
            'account_name': account_name
        }
    }
    logger.debug(f'Сформировано presence сообщение для пользователя {account_name}')
    return out


@log
def process_response_ans(message):
    logger.debug(f'Разбор приветственного сообщения от сервера: {message}')
    if 'response' in message:
        if message['response'] == 200:
            return '200 : OK'
        elif message['responce'] == 400:
            raise '400 : error'
    raise message['response']

def main(port, addr, client_name):
    print('Консольный месседжер. Клиентский модуль.')
    if not client_name:
        client_name = input('Введите имя пользователя: ')

    logger.info(
        f'Запущен клиент с парамертами: адрес сервера: {addr}, '
        f'порт: {port}, имя пользователя: {client_name}')
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((addr, int(port)))
        send_message(s, create_presence(client_name))
        answer = process_response_ans(get_message(s))
        logger.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
    except json.JSONDecodeError:
        logger.error('Не удалось декодировать полученную Json строку.')
        sys.exit(1)
    except Exception:
        logger.critical(
            f'Не удалось подключиться к серверу {addr}:{port}, '
            f'конечный компьютер отверг запрос на подключение.')
        sys.exit(1)
    else:
        receiver = threading.Thread(target=message_from_server, args=(s, client_name))
        receiver.daemon = True
        receiver.start()

        user_interface = threading.Thread(target=user_interactive, args=(s, client_name))
        user_interface.daemon = True
        user_interface.start()
        logger.debug('Запущены процессы')

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == "__main__":
    try:
        parser = create_parser()
        namespace = parser.parse_args(sys.argv[1:])
        port = namespace.port
        addr = namespace.addr
        client_name = namespace.name
        main(port, addr, client_name)
    except Exception as e:
        logger.critical(e)
