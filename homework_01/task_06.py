"""
6. Создать текстовый файл test_file.txt, заполнить его тремя строками: «сетевое
программирование», «сокет», «декоратор». Проверить кодировку файла по умолчанию.
Принудительно открыть файл в формате Unicode и вывести его содержимое.
"""

import chardet

with open('resurse1.txt', 'rb') as f:
    for line in f:
        e = chardet.detect(line)
        coding = e['encoding']
        line = line.decode(coding).encode('utf-8')
        print(line.decode('utf-8'))
 