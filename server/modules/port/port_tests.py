from lib import test_utils as tu
from lib.database.basic_tables import *
from modules.port.port_database import *
from modules.port.port_functions import *
from lib.database.connection import session as dbsession
import unittest

__unittest = True

class TestPortsRoutine(tu.BasicTest):
    def setUp(self):
        super(TestPortsRoutine, self).setUp()

        hilla = ServerDatabase()
        hilla.name = 'Hilla'
        hilla.save()
        dbsession.commit()

        lakka = ServerDatabase()
        lakka.name = 'Lakka'
        lakka.save()
        dbsession.commit()

        hilla_ports = ServiceGroupDatabase()
        hilla_ports.name = 'Hilla_ports'
        hilla_ports.type = 'port'
        hilla_ports.save()
        dbsession.commit()

        lakka_ports = ServiceGroupDatabase()
        lakka_ports.name = 'Lakka_ports'
        lakka_ports.type = 'port'
        lakka_ports.save()
        dbsession.commit()

        hilla_port = ServiceDatabase()
        hilla_port.name = 'Hilla_port'
        hilla_port.service_group = hilla_ports
        hilla_port.server = hilla
        hilla_port.save()
        dbsession.commit()

        lakka_port = ServiceDatabase()
        lakka_port.name = 'Lakka_port'
        lakka_port.service_group = lakka_ports
        lakka_port.server = hilla
        lakka_port.save()
        dbsession.commit()

        self.sg = hilla_ports
        self.sg2 = lakka_ports

    def create_port(self, user, sgid = None):
        port = PortDatabase()
        port.user_id = user
        if sgid is not None:
            port.service_group_id = sgid
        else:
            port.service_group_id = self.sg.id
        port.port = 5678
        port.save()
        dbsession.commit()
        return port

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
        self.assertContainsNone(ServiceGroupDatabase, ServiceGroupDatabase.id == 123)
        self.assertQ('/ports', user=None, method='POST', status=tu.STATUS_NOAUTH, args={'service_group_id': 123})

    def test_ports_push_user_noperms(self):
        u = self.user('test', [])
        self.assertQ('/ports', user=u, method='POST', status=tu.STATUS_DENIED)
        self.assertQ('/ports/', user=u, method='POST', status=tu.STATUS_DENIED)        

    def test_ports_push_user_invalid_server(self):
        u = self.user('test', ['ports_modify_own'])
        self.assertContainsNone(ServiceGroupDatabase, ServiceGroupDatabase.id == 123)
        self.assertQ('/ports', user=u, method='POST', status=tu.STATUS_NOTFOUND, args={'service_group_id': 123})
        self.assertQ('/ports/', user=u, method='POST', status=tu.STATUS_NOTFOUND, args={'service_group_id': 123})
        self.assertContainsNone(PortDatabase)

    def test_ports_push_user(self):
        u = self.user('test', ['ports_modify_own'])
        self.assertContainsNone(PortDatabase, PortDatabase.user_id == u.user.id)
        self.assertQ('/ports', user=u, method='POST', status=tu.STATUS_OK, args={'service_group_id': self.sg.id})
        self.assertContainsOne(PortDatabase, PortDatabase.user_id == u.user.id)
        self.assertQ('/ports/', user=u, method='POST', status=tu.STATUS_OK, args={'service_group_id':self.sg.id})
        self.assertContainsMany(PortDatabase, PortDatabase.user_id == u.user.id)

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
        p = self.create_port(u2.user.id)
        self.assertContainsOne(PortDatabase, PortDatabase.id == p.id)
        self.assertQ('/ports/%d' % (p.id), user=u, method='DELETE', status=tu.STATUS_NOTFOUND) 
        self.assertContainsOne(PortDatabase, PortDatabase.id == p.id)

    def test_delete(self):
        u = self.user("test", ['ports_delete_own'])
        p = self.create_port(u.user.id)
        self.assertContainsOne(PortDatabase, PortDatabase.id == p.id)
        self.assertQ('/ports/%d' % (p.id), user=u, method='DELETE', status=tu.STATUS_OK)
        self.assertContainsNone(PortDatabase, PortDatabase.id == p.id)

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
        self.assertQ('/%d/ports' % (u.user.id), user=a, status=tu.STATUS_OK)
        self.assertQ('/%d/ports/' % (u.user.id), user=a, status=tu.STATUS_OK)

    def test_admin_ports_get_invalid_user(self):
        a = self.user('admiina', ['ports_view_all'])
        self.assertQ('/%d/ports' % (a.user.id + 1), user=a, status=tu.STATUS_NOTFOUND)
        self.assertQ('/%d/ports/' % (a.user.id + 1), user=a, status=tu.STATUS_NOTFOUND)

    def test_admin_ports_push_user_anon(self):
        self.assertQ('/1/ports', user=None, method='POST', status=tu.STATUS_NOAUTH, args={'service_group_id': 123})

    def test_admin_ports_push_user_noperms(self):
        u = self.user('test', [])
        self.assertQ('/%d/ports' % (u.user.id), user=u, method='POST', status=tu.STATUS_DENIED)
        self.assertQ('/%d/ports/' % (u.user.id), user=u, method='POST', status=tu.STATUS_DENIED)

    def test_admin_ports_push_invalid_user(self):
        a = self.user('admiina', ['ports_modify_all'])
        self.assertQ('/%d/ports' % (a.user.id + 1), user=a, method='POST', status=tu.STATUS_NOTFOUND, args={'service_group_id': self.sg.id})
        self.assertQ('/%d/ports/' % (a.user.id + 1), user=a, method='POST', status=tu.STATUS_NOTFOUND, args={'service_group_id': self.sg.id})

    def test_admin_ports_push_user_invalid_server(self):
        u = self.user('test', [])
        a = self.user("admiina", ['ports_modify_all'])
        self.assertContainsNone(ServiceGroupDatabase, ServiceGroupDatabase.id == 123)
        self.assertQ('/1/ports', user=a, method='POST', status=tu.STATUS_NOTFOUND, args={'service_group_id': 123})
        self.assertQ('/1/ports/', user=a, method='POST', status=tu.STATUS_NOTFOUND, args={'service_group_id': 123})

    def test_admin_ports_push_user(self):
        u = self.user('test', [])
        a = self.user("admiina", ['ports_modify_all'])
        self.assertQ('/1/ports', user=a, method='POST', status=tu.STATUS_OK, args={'service_group_id': self.sg.id})
        self.assertQ('/1/ports/', user=a, method='POST', status=tu.STATUS_OK, args={'service_group_id': self.sg.id})

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
        p = self.create_port(u.user.id)
        self.assertQ('/%d/ports/%d' % (u.user.id, p.id), user=a, method='DELETE', status=tu.STATUS_OK)

    """
    GENERIC TESTS
    """
    def test_port_numbering_same_server(self):
        u = self.user("test", [])
        u2 = self.user("test2", [])

        p1 = add_user_port(u.user.id, self.sg.id)
        p2 = add_user_port(u.user.id, self.sg.id)
        p3 = add_user_port(u2.user.id, self.sg.id)
        p4 = add_user_port(u.user.id, self.sg.id)
        self.assertTrue(p1.port == p2.port - 1)
        self.assertTrue(p2.port == p3.port - 1)
        self.assertTrue(p3.port == p4.port - 1)

    def test_port_numbering_different_server(self):
        u = self.user("test", [])

        p1 = add_user_port(u.user.id, self.sg.id)
        p2 = add_user_port(u.user.id, self.sg2.id)
        p3 = add_user_port(u.user.id, self.sg.id)
        p4 = add_user_port(u.user.id, self.sg2.id)

        self.assertTrue(p1.port == p2.port)
        self.assertTrue(p3.port == p4.port)

        self.assertTrue(p1.port == p3.port - 1)
        
if __name__ == "__main__":
    import unittest
    unittest.main()
