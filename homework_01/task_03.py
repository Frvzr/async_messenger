"""
3. Определить, какие из слов «attribute», «класс», «функция», «type» невозможно записать в
байтовом типе.
"""


var1 = b'attribute'
var2 = b'класс'
var3 = b'функция'
var4 = b'type' 

"""
    var2 = b'класс', var3 = b'функция'
                        ^
SyntaxError: bytes can only contain ASCII literal characters.
"""
