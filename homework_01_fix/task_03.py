"""
3. Определить, какие из слов «attribute», «класс», «функция», «type» невозможно записать в
байтовом типе.
"""

var_list = ['attribute', 'класс', 'функция', 'type']

for var in var_list:
    try:
        b = bytes(var, encoding="ascii") # если encoding="utf-8" то работает без ошибок
    except UnicodeEncodeError:
        print('Incorrect coding')
    print(b)
    