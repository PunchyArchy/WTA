""" Модуль содержит обработчики для разных видов данных. """

from wtas.main import WTAS, WTADB
from wtas.functions import no_operator


class TrashCatsS(WTAS):
    """ Оператор передачи данных в AR. """

    def send(self, name, wserver_id, *args, **kwargs):
        self.add_trash_cat(cat_name=name, wserver_id=wserver_id)


class TrashCatsDB(WTADB):
    """ Оператор обработки ответа от AR. """

    def __init__(self, *args, **kwargs):
        super().__init__(table_name='trash_cats_send_reports',
                         column_name='trash_cat', *args, **kwargs)


class TrashTypesS(WTAS):
    """ Оператор передачи данных в AR. """

    def send(self, name, wserver_id, cat_id, *args, **kwargs):
        self.add_trash_type(type_name=name, wserver_id=wserver_id,
                            wserver_cat_id=cat_id)


class TrashTypesDB(WTADB):
    """ Оператор обработки ответа от AR. """

    def __init__(self, *args, **kwargs):
        super().__init__(table_name='trash_types_send_reports',
                         column_name='trash_type', *args, **kwargs)


class CompaniesS(WTAS):
    """ Оператор передачи данных в AR. """

    def send(self, name, inn=None, kpp=None, ex_id=None, status=None,
             wserver_id=None, *args, **kwargs):
        self.add_carrier(name, inn, kpp, ex_id, status, wserver_id)


class CompaniesDB(WTADB):
    """ Оператор обработки ответа от AR. """

    def __init__(self, *args, **kwargs):
        super().__init__(table_name='companies_send_reports',
                         column_name='company', *args, **kwargs)


class AutoS(WTAS):
    """ Оператор передачи данных в AR. """

    def send(self, car_number, wserver_id, model, rfid, id_type,
             rg_weight):
        self.add_auto(car_number, wserver_id, model, rfid, id_type,
                      rg_weight)


class AutoDB(WTADB):
    """ Оператор обработки ответа от AR. """

    def __init__(self, *args, **kwargs):
        super().__init__(table_name='auto_send_reports',
                         column_name='auto', *args, **kwargs)


class UserS(WTAS):
    """ Оператор передачи данных в AR. """

    def send(self, full_name, username, password, wserver_id):
        self.add_operator(full_name, username, password, wserver_id)


class UserDB(WTADB):
    """ Оператор обработки ответа от AR. """

    def __init__(self, *args, **kwargs):
        super().__init__(table_name='operators_send_reports',
                         column_name='operator', *args, **kwargs)


class GetOperator:
    """ Класс, который возвращает объекты для отправки данных на AR и обработку
    ответов. Главным компонентом является атрибут operators, который содержит
    в форме ключей названия данных (в строковом представлении), имеюющих
    следующую структуру:
        'operation_name': {'wtas': Object, 'wtadb': Object},
    Где значением ключа wtas является подкласс WTAS, предназначенный для
    обмена данными между WServer и AR, а ключом wtadb - подкласс WTADB, который
    отвечает за работу с БД."""

    def __init__(self):
        self.operators = {'trash_cats':
                              {'wtas': TrashCatsS,
                               'wtadb': TrashCatsDB},
                          'trash_types':
                              {'wtas': TrashTypesS,
                               'wtadb': TrashTypesDB},
                          'companies':
                              {'wtas': CompaniesS,
                               'wtadb': CompaniesDB},
                          'auto': {'wtas': AutoS,
                                   'wtadb': AutoDB},
                          'users': {'wtas': UserS,
                                    'wtadb': UserDB},
                          }

    @no_operator
    def get_wtas(self, name):
        """
        Вернуть объект класса WTADB.

        :param name: Название данных.
        :return:
        """
        return self.operators[name]['wtas']

    @no_operator
    def get_wtadb(self, name):
        """
        Вернуть объект класса WTADB.

        :param name: Название данных.
        :return:
        """
        return self.operators[name]['wtadb']

    def expand_operators(self, new_operator):
        """
        Расширить словарь операторов.

        :param new_operator: Словарь вида:
            {'name': {'wtas': object, 'wtadb': object}}
        :return: Возвращает обновленный список операторов.
        """
        return self.operators.update(new_operator)


class WTA(GetOperator):
    """ Класс, объединяющий классы для работы с БД и с AR. Предоставляет один
    интерфейс (метод deliver),
    который делает всю работу по отправке данных, и фиксации  этого события.
    По сути - god-object (плохо, да, но до жути удобно).
    """

    def __init__(self, name, *args, **kwargs):
        """
        Инициализация.

        :param name: Имя для оператора
        """
        super(WTA, self).__init__(*args, **kwargs)
        self.wtas, self.wtadb = self.get_operators(name)

    def operate_response(self, response, report_id):
        """ Обработчиков ответа от GCore
        :param response: Сам ответ.
        :param report_id: ID отчета об отправке.
        :return: Возвращает True, при успешном выполнении кода. """
        if response['info']['status'] == 'success':
            self.wtadb.mark_get(wdb_id=response['info']['info'][0][0],
                                report_id=report_id)
        else:
            self.wtadb.mark_fail(response['info']['info'], report_id)
        return True

    def get_operators(self, name):
        """ Получить объекты для работы с БД и с GCore по названию.
        :param name: Название данных.
        :return: Если объекты предусмотрены - вернет True.
        """
        wtas_class = self.get_wtas(name)
        wtadb_class = self.get_wtadb(name)
        wtadb = wtadb_class(dbname='gdb', user='watchman',
                            password='hect0r1337',
                            host='192.168.100.118',
                            polygon_id=9)
        pol_info = wtadb.fetch_polygon_info()
        wtas = wtas_class(polygon_ip=pol_info['ip'],
                          polygon_port=pol_info['port'])
        return wtas, wtadb

    def deliver(self, wserver_id, *args, **kwargs):
        """ Доставить данные до GCore. Отметить успешность доставки.
        :param wserver_id: Обязательный аругемент, ID данных в GDB.
        :return: Если все успешно - вернет True """
        self.wtas.send(wserver_id=wserver_id, *args, **kwargs)
        report_id = self.wtadb.mark_send(gdb_id=wserver_id)
        response = self.wtas.get()
        res = self.operate_response(response, report_id)
        return res
