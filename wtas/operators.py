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

    def send(self, name, wserver_id, trash_cat_id, *args, **kwargs):
        self.add_trash_type(type_name=name, wserver_id=wserver_id,
                            wserver_cat_id=trash_cat_id)


class TrashTypesSUPD(WTAS):
    """ Оператор передачи о обновлении вида груза в AR. """

    def send(self, type_id, new_name, new_cat_id, active, *args, **kwargs):
        self.upd_trash_type(type_id=type_id, name=new_name,
                            category=new_cat_id, active=active)


class TrashTypesDB(WTADB):
    """ Оператор обработки ответа от AR об обновлении вида груза """

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

    def send(self, car_number, wserver_id, model=None, rfid=None, rfid_id=None,
             id_type=None, rg_weight=None, *args, **kwargs):
        self.add_auto(car_number=car_number, wserver_id=wserver_id,
                      model=model, id_type=id_type, rg_weight=rg_weight,
                      rfid=rfid, rfid_id=rfid_id)


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
                          'trash_types_upd':
                              {'wtas': TrashTypesSUPD,
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
    def get_wtas_class(self, name):
        """
        Вернуть объект класса WTADB.

        :param name: Название данных.
        :return:
        """
        return self.operators[name]['wtas']

    @no_operator
    def get_wtadb_class(self, name):
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

    def __init__(self, name, dbname, user, password, host, polygon_id,
                 *args, **kwargs):
        """
        Инициализация.

        :param name: Название вида данных.
        :param dbname: Имя базы данных (GDB).
        :param user: Имя пользователя БД.
        :param password: Пароль пользователя БД.
        :param host: Адрес машины, на котором хостится БД.
        :param polygon_id: ID полигона, куда отправить данные.
        :param args:
        :param kwargs:
        """
        super(WTA, self).__init__(*args, **kwargs)
        self.wtadb = self.get_wtadb(name, dbname, user, password, host,
                                    polygon_id)
        pol_info = self.wtadb.fetch_polygon_info()
        self.wtas = self.get_wtas(name, pol_info['ip'], pol_info['port'])

    def operate_response(self, ar_response, report_id, wserver_id):
        """ Обработчиков ответа от GCore
        :param wserver_id: ID в GDB.
        :param ar_response: Сам ответ.
        :param report_id: ID отчета об отправке.
        :return: Возвращает словарь со статусом выполнения. """
        response = {}
        response['report_id'] = report_id
        response['wserver_id'] = wserver_id
        if ar_response['info']['status'] == 'success':
            self.wtadb.mark_get(wdb_id=ar_response['info']['info'][0][0],
                                report_id=report_id)
            response['success_save'] = True
        else:
            response['success_save'] = False
            self.wtadb.mark_fail(ar_response['info']['info'], report_id)
        return response

    def get_wtadb(self, name, dbname, user, password, host, polygon_id):
        """
        Вернуть инстанс класса WTADB, предназначенный для работы с данными вида
        name.
        :param name: Название вида данных.
        :param dbname: Имя базы данных (GDB).
        :param user: Имя пользователя БД.
        :param password: Пароль пользователя БД.
        :param host: Адрес машины, на котором хостится БД.
        :param polygon_id: ID полигона, куда отправить данные.
        :return:
        """
        wtadb_class = self.get_wtadb_class(name)
        wtadb = wtadb_class(dbname=dbname, user=user,
                            password=password,
                            host=host,
                            polygon_id=polygon_id)
        return wtadb

    def get_wtas(self, name, polygon_ip, polygon_port):
        """ Получить объекты для работы с БД и с GCore по названию.

        :param name: Название данных.
        :param polygon_ip: IP GCore QDK.
        :param polygon_port: Порт GCore QDK.
        :return: Если объекты предусмотрены - вернет True.
        """
        wtas_class = self.get_wtas_class(name)
        wtas = wtas_class(polygon_ip=polygon_ip,
                          polygon_port=polygon_port)
        return wtas

    def deliver(self, wserver_id, *args, **kwargs):
        """ Доставить данные до GCore. Отметить успешность доставки.
        :param wserver_id: Обязательный аругемент, ID данных в GDB.
        :return: Если все успешно - вернет True """
        self.wtas.send(wserver_id=wserver_id, *args, **kwargs)
        report_id = self.wtadb.mark_send(gdb_id=wserver_id)
        response = self.wtas.get()
        res = self.operate_response(response, report_id, wserver_id)
        return res
