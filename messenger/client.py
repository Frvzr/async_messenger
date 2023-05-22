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
from metaclasses import ClientVerifier


logger = client_log_config.get_logger(__name__)

# Парсер аргументов коммандной строки
@log
def create_parser():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument ('-p', '--port', default=7777, help='TCP port for work, default 7777')
        parser.add_argument ('-a', '--addr', default='localhost', help='Listening IP, default localhost')
        parser.add_argument('-n', '--name', default=None, nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        port = namespace.port
        addr = namespace.addr
        client_name = namespace.name
        
        # проверим подходящий номер порта
        if not 1023 < int(port) < 65536:
            logger.critical(
                f'Попытка запуска клиента с неподходящим номером порта: {port}. Допустимы адреса с 1024 до 65535. Клиент завершается.')
            exit(1)
        return port, addr, client_name
    except Exception as e:
        logger.critical(e)


class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()
        
    # Функция создаёт словарь с сообщением о выходе.
    def create_exit_message(self):
        return {
            'action': 'exit',
            'time': time.time(),
            'account_name': self.account_name
        }
    
    # Функция запрашивает кому отправить сообщение и само сообщение, и отправляет полученные данные на сервер.
    def create_message(self):
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')
        message_dict = {
            'action': 'message',
            'sender': self.account_name,
            'destination': to_user,
            'time': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            'text': message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(self.sock, message_dict)
            logger.info(f'Отправлено сообщение для пользователя {to_user}')
        except:
            logger.critical('Потеряно соединение с сервером.')
            sys.exit(1)
            
    # Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения   
    def run(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                send_message(self.sock, self.create_exit_message())
                print('Завершение соединения.')
                logger.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')
    
    # Функция выводящяя справку по использованию.
    def print_help(self):
        """Функция выводящяя справку по использованию"""
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')


class ClientReceiver(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()
    
    # Основной цикл приёмника сообщений, принимает сообщения, выводит в консоль. Завершается при потере соединения.
    def run(self):
        while True:
            try:
                message = get_message(self.sock)
                if 'action' in message and message['action'] == 'message' and \
                        'sender' in message and 'destination' in message \
                        and 'text' in message and message['destination'] == self.account_name:
                    print(f'\nПолучено сообщение от пользователя {message["sender"]}:'
                        f'\n{message["text"]}')
                    logger.info(f'Получено сообщение от пользователя {message["sender"]}:'
                                f'\n{message["text"]}')
                else:
                    logger.error(f'Получено некорректное сообщение с сервера: {message}')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                logger.critical(f'Потеряно соединение с сервером.')
                break

                
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

def main():
    
    print('Консольный месседжер. Клиентский модуль.')
    
    # Загружаем параметы коммандной строки
    port, addr, client_name = create_parser()
    
    # Если имя пользователя не было задано, необходимо запросить пользователя.
    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')
    logger.info(
        f'Запущен клиент с парамертами: адрес сервера: {addr}, '
        f'порт: {port}, имя пользователя: {client_name}')
    
    # Инициализация сокета и сообщение серверу о нашем появлении
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
        # Если соединение с сервером установлено корректно, запускаем клиенский процесс приёма сообщний
        receiver = ClientReceiver(client_name, s)
        receiver.daemon = True
        receiver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        sender = ClientSender(client_name, s)
        sender.daemon = True
        sender.start()
        logger.debug('Запущены процессы')

        # Watchdog основного цикла, если один из потоков завершён, то значит или потеряно соединение или пользователь
        # ввёл exit. Поскольку все события обработываются в потоках, достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if receiver.is_alive() and sender.is_alive():
                continue
            break


if __name__ == "__main__":
    main()
