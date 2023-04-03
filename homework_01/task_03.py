"""
3. Определить, какие из слов «attribute», «класс», «функция», «type» невозможно записать в
байтовом типе.
"""

var_list = ['attribute', 'класс', 'функция', 'type']

for var in var_list:
    b = bytes(var, encoding="utf8")  # без encoding="utf8" кириллица не работает
    print(b)
