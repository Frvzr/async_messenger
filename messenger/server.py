import select
import socket
from wrapper_server_log import log
from log import server_log_config
import argparse
import sys
import json
import threading
from descriptors import Port
from metaclasses import ServerVerifier
from server_database import ServerDatabase
import configparser
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem

logger = server_log_config.get_logger(__name__)


new_connect = False
thread_lock = threading.Lock()

@log
def create_parser(default_port, default_address):
    """Парсер аргументов коммандной строки.

    Returns:
        _str_: port, address
    """
    parser = argparse.ArgumentParser(description='Start server')
    parser.add_argument ('-a', '--addr', default=default_address, help='Server ip address')
    parser.add_argument ('-p', '--port', default=default_port, type=int, nargs='?', help='TCP - port on the server')
    namespace = parser.parse_args(sys.argv[1:])
    port = namespace.port
    addr = namespace.addr
    return port, addr

class Server(threading.Thread, metaclass=ServerVerifier):
    port = Port()

    def __init__(self, port, addr, database):
        self.addr = addr
        self.port = port
        self.database = database
        

        self.clients = []

        self.messages = []

        self.names = dict()
        super().__init__()
        
        
    def response_socket(self):
        logger.info(
            f'Сервер запущен, порт : {self.port} , адрес: {self.addr}')

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.addr, self.port))
        s.settimeout(0.5)
        
        self.sock = s
        self.sock.listen()
        
    def run(self):
        self.response_socket()

        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Соединение установлено: {client_address}')
                self.clients.append(client)

            recv_lst = []
            send__lst = []
            err_lst = []

            try:
                if self.clients:
                    recv_lst, send_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError as err:
                logger.error(f'Ошибка работы с сокетами: {err}')
            
            if recv_lst:
                for client_with_message in recv_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except Exception:
                        logger.info(f'Клиент {client_with_message.getpeername()} '
                                    f'отключился от сервера.')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)

            for message in self.messages:
                try:
                    self.process_message(message, send_lst)
                except Exception:
                    logger.info(f'Связь с клиентом с именем {message["destinations"]} была потеряна')
                    self.clients.remove(self.names[message['destination']])
                    self.database.user_logout(message['destination'])
                    del self.names[message['destination']]
            self.messages.clear()

    def process_message(self, message, listen_socks):
        if message['destination'] in self.names and self.names[message['destination']] in listen_socks:
            send_message(self.names[message['destination']], message)
            logger.info(f'Сообщение отправлено пользователю {message["destination"]} '
                        f'от пользователя {message["sender"]}.')
        elif message["destination"] in self.names and self.names[message["destination"]] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(
                f'Пользователь {message["destination"]} не найден')
    
    def process_client_message(self, message, client):
        global new_connect
        logger.debug(f'Обработка сообщений клиента : {message}')
        if 'action' in message and message['action'] == 'presence' and \
                'time' in message and 'user' in message:
            if message['user']['account_name'] not in self.names.keys():
                self.names[message['user']['account_name']] = client
                client_ip_addr, client_port = client.getpeername()
                self.database.user_login(message['user']['account_name'], client_ip_addr, client_port)
                response = {'response': 200}
                send_message(client, response)
                with thread_lock:
                    new_connect = True
            else:
                response = {
                    'response': 400,
                    'error': 'Имя пользователя уже занято.'
                }
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        
        elif 'action' in message and message['action'] == 'message' and \
                'destination' in message and 'time' in message \
                and 'sender' in message and 'text' in message:
            self.messages.append(message)
            self.database.process_message(
                message['sender'], message['destination'])
            return
        
        elif 'action' in message and message['action'] == 'exit' and 'account_name' in message:
            self.clients.remove(self.names[message['account_name']])
            self.names[message['account_name']].close()
            del self.names[message['account_name']]
            return
        
        elif 'action'in message and message['action'] == 'get_contacts' and 'user' in message and \
                self.names[message['user']] == client:
            response = {'response': 202}
            response['list_info'] = self.database.get_contacts(message['user'])
            send_message(client, response)
            
        elif 'action' in message and message['action'] == 'add_contact' and 'account_name' in message and 'user' in message \
                and self.names[message['user']] == client:
            self.database.add_contact(message['user'], message['account_name'])
            response = {'response': 200}
            send_message(client, response)

        elif 'action' in message and message['action'] == 'remove_contact' and 'account_name' in message and 'user' in message \
                and self.names[message['user']] == client:
            self.database.remove_contact(message['user'], message['account_name'])
            response = {'response': 200}
            send_message(client, response)
            
        elif 'action' in message and message['action'] == 'users_request' and 'account_name'in message \
                and self.names[message['account_name']] == client:
            response = {'response': 202}
            response['list_info'] = [user[0]
                                   for user in self.database.users_list()]
            send_message(client, response)

        else:
            response = {
                'response': 400,
                'error': None
            }
            response['error'] = 'Запрос некорректен.'
            send_message(client, response)
            return
        
        
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
            
def send_message(sock, message):
    js_message = json.dumps(message)
    encoded_message = js_message.encode(encoding='utf-8')
    sock.send(encoded_message)

def print_help():
    print('Поддерживаемые комманды:')
    print('users - список известных пользователей')
    print('exit - завершение работы сервера.')
    print('help - вывод справки по поддерживаемым командам')

def main():
    
    config = configparser.ConfigParser()
    
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    
    listen_address, listen_port = create_parser(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    database = ServerDatabase(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))
    
    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()
    
    server_app = QApplication(sys.argv)
    main_window = MainWindow()
    
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()
    
    def list_update():
        global new_connect
        if new_connect:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with thread_lock:
                new_connect = False
                
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()
        
    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)
        
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки сохранены успешно.')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')
    
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)
    
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)
        
    server_app.exec_()
        
if __name__ == "__main__":
    main()
    