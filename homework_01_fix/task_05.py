"""
5. Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать результаты из
байтовового в строковый тип на кириллице.
"""
import subprocess
import chardet


args = [['ping', 'yandex.ru'],['ping', 'youtube.com']]

for arg in args:

    arg = subprocess.Popen(arg, stdout=subprocess.PIPE)

    for line in arg.stdout:
        e = chardet.detect(line)
        coding = e['encoding']
        line = line.decode(coding).encode('utf-8')
        print(line.decode('utf-8'))