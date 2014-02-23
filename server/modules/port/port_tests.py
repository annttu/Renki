from lib import test_utils as tu
from lib.database.basic_tables import *
from modules.port.port_database import *
from lib.database.connection import session as dbsession

class TestPortsRoutine(tu.BasicTest):
    def setUp(self):
        super(TestPortsRoutine, self).setUp()

        service = ServiceDatabase()
        service.name = "TestService"
        service.save()
        dbsession.commit()

        self.sg = ServerGroupDatabase()
        self.sg.name = "Lakka"
        self.sg.service = service.id
        self.sg.save()
        dbsession.commit()

        self.sg2 = ServerGroupDatabase()
        self.sg2.name = "Hilla"
        self.sg2.service = service.id
        self.sg2.save()
        dbsession.commit()

    def create_port(self, user):
        port = PortDatabase()
        port.user_id = user
        port.server_group_id = self.sg.id
        port.port = 5678
        port.save()
        dbsession.commit()
        return port.id

    """
    USER TESTS
    """
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

    def test_ports_push_user_anon(self):
        self.assertQ('/ports', user=None, method='POST', status=tu.STATUS_NOAUTH, args={'server_group_id':123})
    def test_ports_push_user_noperms(self):
        u = self.user('test', [])
        self.assertQ('/ports', user=u, method='POST', status=tu.STATUS_DENIED)
        self.assertQ('/ports/', user=u, method='POST', status=tu.STATUS_DENIED)        
    def test_ports_push_user_invalid_server(self):
        u = self.user('test', ['ports_add_own'])
        self.assertQ('/ports', user=u, method='POST', status=tu.STATUS_ERROR, args={'server_group_id':123})
        self.assertQ('/ports/', user=u, method='POST', status=tu.STATUS_ERROR, args={'server_group_id':123})
    def test_ports_push_user(self):
        u = self.user('test', ['ports_add_own'])
        self.assertQ('/ports', user=u, method='POST', status=tu.STATUS_OK, args={'server_group_id':1})
        self.assertQ('/ports/', user=u, method='POST', status=tu.STATUS_OK, args={'server_group_id':1})

    def test_delete_anon(self):
        self.assertQ('/ports/1', user=None, method='DELETE', status=tu.STATUS_NOAUTH)
    def test_delete_noperms(self):
        u = self.user('test')
        self.assertQ('/ports/1', user=u, method='DELETE', status=tu.STATUS_DENIED)
    def test_delete_nonexisting(self):
        u = self.user('test', ['ports_delete_own'])
        self.assertQ('/ports/123', user=u, method='DELETE', status=tu.STATUS_NOTFOUND)
    def test_delete_not_own(self):
        u = self.user("test", ['ports_delete_own'])
        u2 = self.user("test2")
        p = self.create_port(2)
        self.assertQ('/ports/1', user=u, method='DELETE', status=tu.STATUS_NOTFOUND) 
    def test_delete(self):
        u = self.user("test", ['ports_delete_own'])
        p = self.create_port(1)
        self.assertQ('/ports/1', user=u, method='DELETE', status=tu.STATUS_OK)

    """
    ADMIN TESTS
    """
    def test_admin_ports_get_user_anon(self):
        u = self.user("test", [])
        self.assertQ('/1/ports', user=None, status=tu.STATUS_NOAUTH)
        self.assertQ('/1/ports/', user=None, status=tu.STATUS_NOAUTH)
    def test_admin_ports_get_user_no_perms(self):
        u = self.user('test', [])
        self.assertQ('/1/ports', user=u, status=tu.STATUS_DENIED)
        self.assertQ('/1/ports/', user=u, status=tu.STATUS_DENIED)
    def test_admin_ports_get_user_wrong_perms(self):
        u = self.user('test', ['ports_view_own'])
        self.assertQ('/1/ports', user=u, status=tu.STATUS_DENIED)
        self.assertQ('/1/ports/', user=u, status=tu.STATUS_DENIED)
    def test_admin_ports_get_user(self):
        u = self.user('test', [])
        a = self.user("admiina", ['ports_view_all'])
        self.assertQ('/1/ports', user=a, status=tu.STATUS_OK)
        self.assertQ('/1/ports/', user=a, status=tu.STATUS_OK)

    def test_admin_ports_push_user_anon(self):
        self.assertQ('/1/ports', user=None, method='POST', status=tu.STATUS_NOAUTH, args={'server_group_id':123})
    def test_admin_ports_push_user_noperms(self):
        u = self.user('test', [])
        self.assertQ('/1/ports', user=u, method='POST', status=tu.STATUS_DENIED)
        self.assertQ('/1/ports/', user=u, method='POST', status=tu.STATUS_DENIED)        
    def test_admin_ports_push_user_invalid_server(self):
        u = self.user('test', [])
        a = self.user("admiina", ['ports_add_all'])
        self.assertQ('/1/ports', user=a, method='POST', status=tu.STATUS_ERROR, args={'server_group_id':123})
        self.assertQ('/1/ports/', user=a, method='POST', status=tu.STATUS_ERROR, args={'server_group_id':123})
    def test_admin_ports_push_user(self):
        u = self.user('test', [])
        a = self.user("admiina", ['ports_add_all'])
        self.assertQ('/1/ports', user=a, method='POST', status=tu.STATUS_OK, args={'server_group_id':1})
        self.assertQ('/1/ports/', user=a, method='POST', status=tu.STATUS_OK, args={'server_group_id':1})

    def test_admin_delete_anon(self):
        self.assertQ('/1/ports/1', user=None, method='DELETE', status=tu.STATUS_NOAUTH)
    def test_admin_delete_noperms(self):
        u = self.user('test', [])
        self.assertQ('/1/ports/1', user=u, method='DELETE', status=tu.STATUS_DENIED)
    def test_admin_delete_nonexisting(self):
        a = self.user('admiina', ['ports_delete_all'])
        self.assertQ('/1/ports/123', user=a, method='DELETE', status=tu.STATUS_NOTFOUND)
    def test_admin_delete_not_own(self):
        u = self.user("test", [])
        a = self.user("admiina", ['ports_delete_all'])
        p = self.create_port(1)
        self.assertQ('/1/ports/1', user=a, method='DELETE', status=tu.STATUS_OK) 
    def test_admin_delete(self):
        u = self.user("test", [])
        a = self.user("admiina", ['ports_delete_all'])
        p = self.create_port(1)
        self.assertQ('/1/ports/1', user=a, method='DELETE', status=tu.STATUS_OK)

if __name__ == "__main__":
    import unittest
    unittest.main()
