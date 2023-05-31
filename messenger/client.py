import os
import sys
curDir = os.getcwd()
sys.path.append(curDir)
from log import client_log_config
from wrapper_client_log import log
import argparse
import sys
from PyQt5.QtWidgets import QApplication
from vars import *
from errors import ServerError
from client.database import ClientDatabase
from client.transport import ClientSender
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog


logger = client_log_config.get_logger(__name__)

@log
def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-p', '--port', default=DEFAULT_PORT, type=int, help='TCP port for work, default 7777')
    parser.add_argument ('-a', '--addr', default=DEFAULT_IP_ADDRESS, help='Listening IP, default localhost')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    port = namespace.port
    addr = namespace.addr
    client_name = namespace.name
        
    if not 1023 < int(port) < 65536:
        logger.critical(
            'Допустимы адреса с 1024 до 65535.')
        exit(1)
        
    return port, addr, client_name


if __name__ == '__main__':
    port, addr, client_name = create_parser()

    client_app = QApplication(sys.argv)

    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    logger.info(
        f'Запущен клиент: адрес сервера: {addr} , порт: {port}, имя пользователя: {client_name}')

    database = ClientDatabase(client_name)
    
    try:
        transport = ClientSender(port, addr, database, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()
        