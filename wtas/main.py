"""" WTAS (WServer To AR Sender) - механизм отправки данных с WServer
на AR """

from abc import ABC, abstractmethod
from wsqluse.wsqluse import Wsqluse
from gc_qdk.main import GCoreQDK


class WTAS(ABC, GCoreQDK):
    """
    WServer To AR Sender.
    Абстрактный, основной класс, с которого наследуют иные классы, занимающиеся
    отправкой данных на AR.
    """

    def __init__(self, polygon_ip, polygon_port, *args, **kwargs):
        """
        Инициализация.

        :param name: Имя обработчика.
        :param table_name: Название таблицы в базе данных GDB.
        :param ar_method: Какой метод AR должен вернуть ответ.
        """
        super().__init__(polygon_ip, polygon_port, *args, **kwargs)
        self.make_connection()

    @abstractmethod
    def send(self, *args, **kwargs):
        """ Отправить данные на AR. """
        pass

    def get(self, *args, **kwargs):
        """ Обработать ответ от AR. """
        response = self.get_data()
        return response


class WTADB(ABC, Wsqluse):
    """
    WServer To AR Data Base.
    Абстрактный, основной класс, с которого наследуют иные классы, занимающиеся
    обработкой ответов от AR.
    (Был отделен от WTAS, во имя следования принципу
    Single Responsibility Principle)"""

    def __init__(self, polygon_id, table_name, column_name,
                 *args, **kwargs):
        """
        Инициация.

        """
        super().__init__(*args, **kwargs)
        self.table_name = table_name
        self.column_name = column_name
        self.polygon_id = polygon_id

    def fetch_polygon_info(self):
        """
        Вернуть всю информацию, необходимую для подключения к полигону по его ID

        :return:
        """
        command = "SELECT * FROM wta_connection_info WHERE polygon={}"
        command = command.format(self.polygon_id)
        response = self.get_table_dict(command)
        print("RESS", response)
        if response['status'] == 'success':
            return response['info'][0]

    def mark_get(self, wdb_id, report_id):
        """
        Обрабатывает полученные данные от AR.

        :param wdb_id: ID в WDB, на стороне полигона.
        :param report_id: ID отчета об отправке (как правило, это
            таблица с именем {tablename}_send_reports).
        :return: Результат работы
        """
        command = "UPDATE {} SET get_time=now(), wdb_id={} WHERE id={}"
        command = command.format(self.table_name, wdb_id, report_id)
        response = self.try_execute(command)
        return response

    def mark_fail(self, info, report_id):
        """
        Отметить провал отправки данных на AR.

        :param info: Python Traceback, который вернул AR.
        :param report_id: ID отчета.
        :return:
        """
        command = "UPDATE {} SET get_time=now(), additional='{}' WHERE id={}"
        command = command.format(self.table_name, info, report_id)
        response = self.try_execute(command)
        return response

    def mark_send(self, gdb_id):
        """
        Сделать запись о том, что данные были отправлены.

        :return: ID записи.
        """
        command = "INSERT INTO {} ({}, polygon, send_time) VALUES ({}, {}, " \
                  "now())"
        command = command.format(self.table_name, self.column_name, gdb_id,
                                 self.polygon_id)
        response = self.try_execute(command)
        if response['status'] == 'success':
            return response['info'][0][0]


