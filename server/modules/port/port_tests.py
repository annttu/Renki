from lib import test_utils as tu
from lib.database.basic_tables import *
from lib.database.connection import session as dbsession

class TestPortsRoutine(tu.BasicTest):
    def setUp(self):
        super(TestPortsRoutine, self).setUp()

        service = ServiceDatabase()
        service.name = "TestService"
        service.save()

        sg = ServerGroupDatabase()
        sg.name = "Lakka"
        sg.service = service.id
        sg.save()
    
    def test_ports_get_user_anon(self):
        self.assertQ('/ports', user=None, status=tu.STATUS_NOAUTH)
        self.assertQ('/ports/', user=None, status=tu.STATUS_NOAUTH)
    def test_ports_get_user_no_perms(self):
        u = self.user('test', [])
        self.assertQ('/ports', user=u, status=tu.STATUS_DENIED)
        self.assertQ('/ports/', user=u, status=tu.STATUS_DENIED)
    def test_ports_get_user(self):
        u = self.user('test', ['ports_view_own'])
        self.assertQ('/ports', user=u, status=tu.STATUS_OK)
        self.assertQ('/ports/', user=u, status=tu.STATUS_OK)
    def test_ports_push_user_noperms(self):
        u = self.user('test', [])
        self.assertQ('/ports', user=u, method='POST', status=tu.STATUS_DENIED)
        self.assertQ('/ports/', user=u, method='POST', status=tu.STATUS_DENIED)        
    def test_ports_push_user_invalid_server(self):
        u = self.user('test', ['ports_add_own'])
        self.assertQ('/ports', user=u, method='POST', status=tu.STATUS_ERROR, args={'server_group_id':2})
        self.assertQ('/ports/', user=u, method='POST', status=tu.STATUS_ERROR, args={'server_group_id':2})

if __name__ == "__main__":
    import unittest
    unittest.main()
