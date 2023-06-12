"""
2. Каждое из слов «class», «function», «method» записать в байтовом типе без преобразования в
последовательность кодов (не используя методы encode и decode) и определить тип,
содержимое и длину соответствующих переменных.
"""

var_list_byte = [b'class', b'function', b'method']

for line in var_list_byte:
    print(f'тип переменной: {type(line)}')
    print(f'содержание переменной - {line}')
    print(f'длинна строки: {len(line)}\n')