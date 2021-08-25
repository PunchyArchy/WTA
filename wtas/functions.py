""" Содержит функционал WTAS """


def no_operator(func):
    """
    Декоратор вызова оператора по ключу. Возвращает None, если искомый
    оператор не найден.

    :param func: Функция извлечения WTAS или WTADB.
    :return:
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return None
    return wrapper
