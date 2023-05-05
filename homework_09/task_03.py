"""
    Написать функцию host_range_ping_tab(), возможности которой основаны на функции из
примера 2. Но в данном случае результат должен быть итоговым по всем ip-адресам,
представленным в табличном формате (использовать модуль tabulate). Таблица должна
состоять из двух колонок и выглядеть примерно так:

Reachable
-------------
10.0.0.1
10.0.0.2

Unreachable
-------------
10.0.0.3
10.0.0.4
"""

import ipaddress
import platform
import subprocess
from tabulate import tabulate


def valid_range(first, second):
    return first < second


def host_range_ping(start_ip, end_ip):
    ip_dict = {'Reachable': [], 'Unreachable': []}
    
    system = '-n' if platform.system().lower()=='windows' else '-c'
    check_ip = valid_range(start_ip, end_ip)
    
    if check_ip:
        for ip in range(int(start_ip), int(end_ip)):
            ip = str(ipaddress.ip_address(ip))
            command = ['ping', system, '1', ip]
            
            if subprocess.call(command) == 0:
                ip_dict['Reachable'].append(ip)
            else:
                ip_dict['Unreachable'].append(ip)
        print(tabulate(ip_dict, headers='keys', tablefmt="grid"))
    else:
        print('Конечный IP меньше стартового')
        
    
if __name__ == "__main__":
    start_ip = ipaddress.IPv4Address('10.0.0.1')
    end_ip = ipaddress.IPv4Address('10.0.0.5')
    host_range_ping(start_ip, end_ip)
    