"""
6. Создать текстовый файл test_file.txt, заполнить его тремя строками: «сетевое
программирование», «сокет», «декоратор». Проверить кодировку файла по умолчанию.
Принудительно открыть файл в формате Unicode и вывести его содержимое.
"""

import locale
 
resurs_string = ['сетевое программирование', 'сокет', 'декоратор']
 

with open('resurs.txt', 'w+') as f:
    for i in resurs_string:
        f.write(i + '\n')
    f.seek(0)
 
print(f)
 
file_coding = locale.getpreferredencoding()
 

with open('resurs.txt', 'r', encoding=file_coding) as f:
    for i in f:
        print(i)
 
    f.seek(0)