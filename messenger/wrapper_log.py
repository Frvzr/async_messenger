import logging
from functools import wraps
import inspect
from datetime import datetime


logger_dec = logging.getLogger('client')

def log(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger_name = func.__name__
        fh = logging.FileHandler('client.log', encoding='utf-8')
        logger_dec.addHandler(fh)
        logger_dec.setLevel(logging.INFO)
        
        res = func(*args, **kwargs)
        logger_dec.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M')} - Функция {logger_name} вызвана из функции {inspect.stack()[1][3]}")

        return res
    return wrapper