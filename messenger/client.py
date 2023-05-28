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
from client_database import ClientDatabase


logger = client_log_config.get_logger(__name__)

sock_lock = threading.Lock()
database_lock = threading.Lock()

class ServerError(Exception):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text
    
class IncorrectDataRecivedError(Exception):
    def __str__(self):
        return 'Принято некорректное сообщение от удалённого компьютера.'
    
class ReqFieldMissingError(Exception):
    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'В принятом словаре отсутствует обязательное поле {self.missing_field}.'


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
        
        if not 1023 < int(port) < 65536:
            logger.critical(
                f'Попытка запуска клиента с неподходящим номером порта: {port}. Допустимы адреса с 1024 до 65535. Клиент завершается.')
            exit(1)
        return port, addr, client_name
    except Exception as e:
        logger.critical(e)


class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def create_exit_message(self):
        return {
            'action': 'exit',
            'time': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            'account_name': self.account_name
        }
    
    def create_message(self):
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')
        
        with database_lock:
            if not self.database.check_user(to_user):
                logger.error(f'Попытка отправить сообщение незарегистрированому получателю: {to_user}')
                return
        
        message_dict = {
            'action': 'message',
            'sender': self.account_name,
            'destination': to_user,
            'time': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            'text': message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')
        
        with database_lock:
            self.database.save_message(self.account_name , to_user , message)
        
        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                logger.info(f'Отправлено сообщение для пользователя {to_user}')
            except OSError as err:
                if err.errno:
                    logger.critical('Потеряно соединение с сервером.')
                    exit(1)
                else:
                    logger.error('Не удалось передать сообщение. Таймаут соединения')
   
    def run(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_exit_message())
                    except:
                        pass
                    print('Завершение соединения.')
                    logger.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                    print(contacts_list)
                for contact in contacts_list:
                    print(contact)
            elif command == 'edit':
                self.edit_contacts()
            elif command == 'history':
                self.print_history()
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')
    
    def print_help(self):
        """Функция выводящяя справку по использованию"""
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} от {message[3]}\n{message[2]}')
    
    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logger.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                
                try:
                    add_contact(self.sock , self.account_name, edit)
                except ServerError:
                    logger.error('Не удалось отправить информацию на сервер.')
 
@log
def process_response_ans(message):
    logger.debug(f'Разбор приветственного сообщения от сервера: {message}')
    if 'response' in message:
        if message['response'] == 200:
            return '200 : OK'
        elif message['responce'] == 400:
            raise '400 : error'
    raise message['response']     
                  
                        
class ClientReceiver(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()
    
    def run(self):
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)

                except IncorrectDataRecivedError:
                    logger.error(f'Не удалось декодировать полученное сообщение.')
                except OSError as err:
                    if err.errno:
                        logger.critical(f'Потеряно соединение с сервером.')
                        break
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    logger.critical(f'Потеряно соединение с сервером.')
                    break
                else:
                    if 'action' in message and message['action'] == 'message' and 'sender' in message and 'destination' in message \
                            and 'text' in message and message['destinaion'] == self.account_name:
                        print(f"\nПолучено сообщение от пользователя {message['sender']}:\n{message['text']}")
                        with database_lock:
                            try:
                                self.database.save_message(message['sender'], self.account_name, message['text'])
                            except:
                                logger.error('Ошибка взаимодействия с базой данных')

                        logger.info(f"Получено сообщение от пользователя {message['sender']}:\n{message['text']}")
                    else:
                        logger.error(f'Получено некорректное сообщение с сервера: {message}')

                
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

def contacts_list_request(sock, name):
    logger.debug(f'Запрос контакт листа для пользователся {name}')
    req = {
        'action': 'get_contacts',
        'time': time.time(),
        'user': name
    }
    logger.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    answer = get_message(sock)
    logger.debug(f'Получен ответ {answer}')
    if 'response' in answer and answer['response'] == 202:
        return answer['list_info']
    else:
        raise ServerError('ServerError')

def add_contact(sock, username, contact):
    logger.debug(f'Создание контакта {contact}')
    req = {
        'action': 'add_contact',
        'time': time.time(),
        'user': username,
        'account_name': contact
    }
    send_message(sock, req)
    answer = get_message(sock)
    if 'response' in answer and answer['response'] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Удачное создание контакта.')
    
def user_list_request(sock, username):
    logger.debug(f'Запрос списка известных пользователей {username}')
    req = {
        'action': 'users_request',
        'time': time.time(),
        'account_name': username
    }
    send_message(sock, req)
    ans = get_message(sock)
    if 'response' in ans and ans['response'] == 202:
        return ans['list_info']
    else:
        raise ServerError('Server Error')

def remove_contact(sock, username, contact):
    logger.debug(f'Создание контакта {contact}')
    req = {
        'action': 'remove_contact',
        'time': time.time(),
        'user': username,
        'account_name': contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if 'response' in ans and ans['response'] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления клиента')
    print('Удачное удаление')
    
def database_load(sock, database, username):
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        logger.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        logger.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)

def main():
    print('Консольный месседжер. Клиентский модуль.')
    port, addr, client_name = create_parser()
    
    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')
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
        exit(1)
    except ServerError as error:
        logger.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        exit(1)
    except ReqFieldMissingError as missing_error:
        logger.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        logger.critical(
            f'Не удалось подключиться к серверу {addr}:{port}, конечный компьютер отверг запрос на подключение.')
        exit(1)
    else:
        
        database = ClientDatabase(client_name)
        database_load(s, database, client_name)
        
        
        sender = ClientSender(client_name, s, database)
        sender.daemon = True
        sender.start()
        logger.info('Запущены процессы')

        receiver = ClientReceiver(client_name, s, database)
        receiver.daemon = True
        receiver.start()
        
        while True:
            time.sleep(1)
            if receiver.is_alive() and sender.is_alive():
                continue
            break


if __name__ == "__main__":
    main()
