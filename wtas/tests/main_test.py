from wtas import operators
import unittest


class MainTest(unittest.TestCase):
    def test_companies(self):
        wtas, wtadb = self.get_operators('companies')
        wtas.send(name='test_company_1', wserver_id=507970, inn=123,
                  kpp=31231)
        report_id = wtadb.mark_send(gdb_id=507970)
        response = wtas.get()
        res = self.operate_response(wtadb, response, report_id)
        self.assertTrue(res)

    def test_companies2(self):
        wta = operators.WTA('companies', 'gdb', 'watchman', 'hect0r1337',
                            '192.168.100.118', 9)
        res = wta.deliver(name='test_company_1', wserver_id=507970, inn=123,
                          kpp=31231)
        self.assertTrue(res)

    def test_auto(self):
        wtas, wtadb = self.get_operators('auto')
        wtas.send(car_number='В060ХА702', id_type='rfid', rg_weight=0,
                  model=0, rfid='1241241241', wserver_id=10480)
        report_id = wtadb.mark_send(gdb_id=10480)
        response = wtas.get()
        res = self.operate_response(wtadb, response, report_id)
        self.assertTrue(res)

    def test_trash_types(self):
        wtas, wtadb = self.get_operators('trash_types')
        wtas.send('Test_type_1', 52, 5)
        report_id = wtadb.mark_send(gdb_id=52)
        response = wtas.get()
        res = self.operate_response(wtadb, response, report_id)
        self.assertTrue(res)

    def test_trash_cats(self):
        wtas, wtadb = self.get_operators('trash_cats')
        wtas.send('test_trash_cat_1', 37)
        report_id = wtadb.mark_send(gdb_id=37)
        response = wtas.get()
        res = self.operate_response(wtadb, response, report_id)
        self.assertTrue(res)

    def test_users(self):
        wtas, wtadb = self.get_operators('users')
        wtas.send('Элверт', 'Эльверт', '1241241', 14160)
        report_id = wtadb.mark_send(gdb_id=14160)
        response = wtas.get()
        res = self.operate_response(wtadb, response, report_id)
        self.assertTrue(res)

    def operate_response(self, wtadb, response, report_id):
        if response['info']['status'] == 'success':
            wtadb.mark_get(wdb_id=response['info']['info'][0][0],
                           report_id=report_id)
        else:
            wtadb.mark_fail(response['info']['info'], report_id)
        return True

    def get_operators(self, name):
        wtas_class = operators.GetOperator().get_wtas_class(name)
        wtadb_class = operators.GetOperator().get_wtadb_class(name)
        wtadb = wtadb_class(dbname='gdb', user='watchman',
                            password='hect0r1337',
                            host='192.168.100.118',
                            polygon_id=9)
        pol_info = wtadb.fetch_polygon_info()
        wtas = wtas_class(polygon_ip=pol_info['ip'],
                          polygon_port=pol_info['port'])
        return wtas, wtadb


if __name__ == '__unittest__':
    unittest.main()
