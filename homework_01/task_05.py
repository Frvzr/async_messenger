"""
5. Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать результаты из
байтовового в строковый тип на кириллице.
"""
import subprocess
 

args = [['ping', 'yandex.ru'],['ping', 'youtube.com']]
 
for arg in args:
 
    arg = subprocess.Popen(arg, stdout=subprocess.PIPE)
 
    for line in arg.stdout:
        line = line.decode('cp866').encode('utf-8')
        print(line.decode('utf-8'))