"""
Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
Меняться должен только последний октет каждого адреса. По результатам проверки должно
выводиться соответствующее сообщение.
"""

import ipaddress
import platform
import subprocess

def valid_range(first, second):
    return first < second


def host_range_ping(ip):
    
    system = '-n' if platform.system().lower()=='windows' else '-c'
    command = ['ping', system, '1', str(ip)]
    
    if subprocess.call(command) == 0:
        print(f'Узел c {ip} доступен')
    else:
        print(f'Узел {ip} недоступен или не существует')


if __name__ == "__main__":
    try:
        start_ip = ipaddress.IPv4Address('192.168.0.10')
        end_ip = ipaddress.IPv4Address('192.168.0.20')
        check_ip = valid_range(start_ip, end_ip)
        if check_ip:
            for ip in range(int(start_ip), int(end_ip)):
                host_range_ping(ip)
        else:
            print('Конечный IP меньше стартового ')
    except Exception as e:
        print('Неверный IP')
        