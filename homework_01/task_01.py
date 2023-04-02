"""
1. Каждое из слов «разработка», «сокет», «декоратор» представить в строковом формате и
проверить тип и содержание соответствующих переменных. Затем с помощью
онлайн-конвертера преобразовать строковые представление в формат Unicode и также
проверить тип и содержимое переменных.
"""

var_list_str = ['разработка', 'сокет', 'декоратор']
 
for line in var_list_str:
    print(f'тип переменной: {type(line)}')
    print(f'содержание переменной - {line}')
    print(f'длинна строки: {len(line)}\n')

var_list_utf  = ['\xd1\x80\xd0\xb0\xd0\xb7\xd1\x80\xd0\xb0\xd0\xb1\xd0\xbe\xd1\x82\xd0\xba\xd0\xb0',
	'\xd1\x81\xd0\xbe\xd0\xba\xd0\xb5\xd1\x82',
	'\xd0\xb4\xd0\xb5\xd0\xba\xd0\xbe\xd1\x80\xd0\xb0\xd1\x82\xd0\xbe\xd1\x80']

for line in var_list_utf:
    print(f'тип переменной: {type(line)}')
    print(f'содержание переменной - {line}')
    print(f'длинна строки: {len(line)}\n')