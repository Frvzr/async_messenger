import select
import socket
from wrapper_server_log import log
from log import server_log_config
import argparse
import sys
import json
from descriptors import Port
from metaclasses import ServerVerifier

logger = server_log_config.get_logger(__name__)


@log
def create_parser():
    """Парсер аргументов коммандной строки.

    Returns:
        _str_: port, address
    """
    try:
        parser = argparse.ArgumentParser(description='Start server')
        parser.add_argument ('-a', '--addr', default='', help='Server ip address, default localhost')
        parser.add_argument ('-p', '--port', default=7777, help='TCP - port on the server, default 7777')
        namespace = parser.parse_args(sys.argv[1:])
        port = namespace.port
        addr = namespace.addr
        return int(port), addr
    except Exception as e:
        logger.critical(e)


class Server(metaclass=ServerVerifier):
    port = Port()

    def __init__(self, port, addr):
        self.addr = addr
        self.port = port
        
        # Список подключённых клиентов.
        self.clients = []
        # Список сообщений на отправку.
        self.messages = []
        # Словарь содержащий сопоставленные имена и соответствующие им сокеты.
        self.names = dict()
        
    def response_socket(self):
        logger.info(
            f'Запущен сервер, порт для подключений: {self.port} , адрес с которого принимаются подключения: {self.addr}. Если адрес не указан, принимаются соединения с любых адресов.')
        # Готовим сокет
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.addr, self.port))
        s.settimeout(0.5)

        # Начинаем слушать сокет.
        self.sock = s
        self.sock.listen()
        
    def main_loop(self):
        # Инициализация Сокета
        self.response_socket()
        
        # Основной цикл программы сервера
        while True:
            # Ждём подключения, если таймаут вышел, ловим исключение.
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соедение: {client_address}')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []

            # Проверяем на наличие ждущих клиентов
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass
            
            # принимаем сообщения и если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except Exception:
                        logger.info(f'Клиент {client_with_message.getpeername()} '
                                    f'отключился от сервера.')
                        self.clients.remove(client_with_message)

            # Если есть сообщения, обрабатываем каждое.
            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except Exception:
                    logger.info(f'Связь с клиентом с именем {message["destinations"]} была потеряна')
                    self.clients.remove(self.names[message['destination']])
                    del self.names[message['destination']]
            self.messages.clear()

    
    # Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение, список зарегистрированых
    # пользователей и слушающие сокеты. Ничего не возвращает.
    def process_message(self, message, listen_socks):
        if message['destination'] in self.names and self.names[message['destination']] in listen_socks:
            send_message(self.names[message['destination']], message)
            logger.info(f'Отправлено сообщение пользователю {message["destination"]} '
                        f'от пользователя {message["sender"]}.')
        elif message["destination"] in self.names and self.names[message["destination"]] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(
                f'Пользователь {message["destination"]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')
    
    # Обработчик сообщений от клиентов, принимает словарь - сообщение от клиента, проверяет корректность, отправляет
    #     словарь-ответ в случае необходимости.
    def process_client_message(self, message, client):
        logger.debug(f'Разбор сообщения от клиента : {message}')
        # Если это сообщение о присутствии, принимаем и отвечаем
        if 'action' in message and message['action'] == 'presence' and \
                'time' in message and 'user' in message:
            # Если такой пользователь ещё не зарегистрирован, регистрируем, иначе отправляем ответ и завершаем соединение.
            if message['user']['account_name'] not in self.names.keys():
                self.names[message['user']['account_name']] = client
                response = {'response': 200}
                send_message(client, response)
            else:
                response = {
                    'response': 400,
                    'error': 'Имя пользователя уже занято.'
                }
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        
        # Если это сообщение, то добавляем его в очередь сообщений. Ответ не требуется.
        elif 'action' in message and message['action'] == 'message' and \
                'destination' in message and 'time' in message \
                and 'sender' in message and 'text' in message:
            self.messages.append(message)
            return
        
        # Если клиент выходит
        elif 'action' in message and message['action'] == 'exit' and 'account_name' in message:
            self.clients.remove(self.names[message['account_name']])
            self.names[message['account_name']].close()
            del self.names[message['account_name']]
            return

        # Иначе отдаём Bad request
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

def main():
    # Загрузка параметров командной строки, если нет параметров, то задаём значения по умоланию.
    port, addr = create_parser() 
    
    # Создание экземпляра класса - сервера.
    server = Server(port, addr)
    server.main_loop()
    

if __name__ == "__main__":
    main()