"""
1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться
доступность сетевых узлов. Аргументом функции является список, в котором каждый сетевой
узел должен быть представлен именем хоста или ip-адресом. В функции необходимо
перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
(«Узел доступен», «Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с
помощью функции ip_address().
"""
import platform  
import subprocess
import ipaddress
import socket

def get_ip(host):
    try:
        ip_host = socket.gethostbyname(host)
        ip = ipaddress.ip_address(ip_host)
        return ip
    except:
        return host

def host_ping(host):
    ip = get_ip(host)
    system = '-n' if platform.system().lower()=='windows' else '-c'
    command = ['ping', system, '1', str(ip)]
    
    if subprocess.call(command) == 0:
        print(f'Узел {host} c {ip} доступен')
    else:
        print(f'Узел {host} недоступен или не существует')


hosts = ['google.com', 'yandex.ru', 'gb.ru', "gbbbbr.ru"]

if __name__ == "__main__":
    for host in hosts:
        host_ping(host)