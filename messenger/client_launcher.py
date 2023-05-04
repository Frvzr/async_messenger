""" 4. Продолжаем работать над проектом «Мессенджер»:
a. Реализовать скрипт, запускающий два клиентских приложения: на чтение чата и на
запись в него. Уместно использовать модуль subprocess);
b. Реализовать скрипт, запускающий указанное количество клиентских приложений.
"""

import subprocess


CLIENTS = []
    
while True:
    command= input('Введите количество клиентов или q для выхода: ')
    if command == 'q':
        print('Пока!')
        break
    elif command.isdigit():
        for client in range(int(command)):
            CLIENTS.append(subprocess.Popen(f'python client.py -n test{client}', creationflags=subprocess.CREATE_NEW_CONSOLE))
    else:
        print('Команда не распознана, попробуйте еще раз')

