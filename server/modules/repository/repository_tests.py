from lib import test_utils as tu
from lib.database.basic_tables import *
from modules.repository.repository_database import *
from modules.repository.repository_functions import *
from modules.repository.repository_validators import *
from lib.database.connection import session as dbsession
import unittest

__unittest = True

class TestRepositoriesRoutine(tu.BasicTest):
    def setUp(self):
        super(TestRepositoriesRoutine, self).setUp()

        service = ServiceDatabase()
        service.name = "TestService"
        service.save()
        dbsession.commit()

        self.sg = ServerGroupDatabase()
        self.sg.name = "Lakka"
        self.sg.service = service
        self.sg.save()
        dbsession.commit()

        self.sg2 = ServerGroupDatabase()
        self.sg2.name = "Hilla"
        self.sg2.service = service
        self.sg2.save()
        dbsession.commit()
    def create_repository(self, user, name, type, sgid = None):
        repo = RepositoryDatabase()
        repo.user_id = user
        if sgid is not None:
            repo.server_group_id = sgid
        else:
            repo.server_group_id = self.sg.id
        repo.name = name
        repo.type = type
        repo.save()
        dbsession.commit()
        return repo
    """
    USER TESTS
    """
    def test_repositories_get_user_anon(self):
        self.assertQ('/repositories', user=None, status=tu.STATUS_NOAUTH)
        self.assertQ('/repositories/', user=None, status=tu.STATUS_NOAUTH)

    def test_repositories_get_user_no_perms(self):
        u = self.user('test', [])
        self.assertQ('/repositories', user=u, status=tu.STATUS_DENIED)
        self.assertQ('/repositories/', user=u, status=tu.STATUS_DENIED)

    def test_repositories_get_user(self):
        u = self.user('test', ['repositories_view_own'])
        self.assertQ('/repositories', user=u, status=tu.STATUS_OK)
        self.assertQ('/repositories/', user=u, status=tu.STATUS_OK)

    def test_repositories_push_user_anon(self):
        self.assertQ('/repositories/svn', user=None, method='POST', status=tu.STATUS_NOAUTH)
        self.assertQ('/repositories/svn/', user=None, method='POST', status=tu.STATUS_NOAUTH)

    def test_repositories_push_user_noperms(self):
        u = self.user('test', [])
        self.assertQ('/repositories/svn', user=u, method='POST', status=tu.STATUS_DENIED)
        self.assertQ('/repositories/svn/', user=u, method='POST', status=tu.STATUS_DENIED)

    def test_repositories_push_user_invalid_server(self):
        u = self.user('test', ['repositories_modify_own'])
        self.assertContainsNone(ServerGroupDatabase, ServerGroupDatabase.id == 123)
        self.assertQ('/repositories/svn', user=u, method='POST', status=tu.STATUS_NOTFOUND, args={'server_group_id': 123, 'name': 'testRepository'})
        self.assertQ('/repositories/svn/', user=u, method='POST', status=tu.STATUS_NOTFOUND, args={'server_group_id': 123, 'name': 'testRepository'})
        self.assertContainsNone(RepositoryDatabase)

    def test_repositories_push_user_invalid_type(self):
        u = self.user('test', ['repositories_modify_own'])
        self.assertQ('/repositories/spudro', user=u, method='POST', status=tu.STATUS_ERROR, args={'server_group_id': self.sg.id, 'name': 'testRepository'})
        self.assertQ('/repositories/spudro/', user=u, method='POST', status=tu.STATUS_ERROR, args={'server_group_id': self.sg.id, 'name': 'testRepository'})
        self.assertContainsNone(RepositoryDatabase)

    def test_repositories_push_user(self):
        u = self.user('test', ['repositories_modify_own'])
        self.assertContainsNone(RepositoryDatabase, RepositoryDatabase.user_id == u.user.id)
        self.assertQ('/repositories/svn', user=u, method='POST', status=tu.STATUS_OK, args={'server_group_id': self.sg.id, 'name': 'testRepository1'})
        self.assertContainsOne(RepositoryDatabase, RepositoryDatabase.user_id == u.user.id)
        self.assertQ('/repositories/svn/', user=u, method='POST', status=tu.STATUS_OK, args={'server_group_id': self.sg.id, 'name': 'testRepository2'})
        self.assertContainsMany(RepositoryDatabase, RepositoryDatabase.user_id == u.user.id)
    
    def test_delete_anon(self):
        self.assertQ('/repositories/svn/1', user=None, method='DELETE', status=tu.STATUS_NOAUTH)

    def test_delete_noperms(self):
        u = self.user('test')
        self.assertQ('/repositories/svn/1', user=u, method='DELETE', status=tu.STATUS_DENIED)

    def test_delete_nonexisting(self):
        u = self.user('test', ['repositories_modify_own'])
        self.assertQ('/repositories/svn/123', user=u, method='DELETE', status=tu.STATUS_NOTFOUND)

    def test_delete_not_own(self):
        u = self.user("test", ['repositories_modify_own'])
        u2 = self.user("test2")
        r = self.create_repository(u2.user.id, 'repo', 'svn')
        self.assertContainsOne(RepositoryDatabase, RepositoryDatabase.id == r.id)
        self.assertQ('/repositories/%s/%d' % (r.type, r.id), user=u, method='DELETE', status=tu.STATUS_NOTFOUND) 
        self.assertContainsOne(RepositoryDatabase, RepositoryDatabase.id == r.id)

    def test_delete(self):
        u = self.user("test", ['repositories_modify_own'])
        r = self.create_repository(u.user.id, 'repo', 'svn')
        self.assertContainsOne(RepositoryDatabase, RepositoryDatabase.id == r.id)
        self.assertQ('/repositories/%s/%d' % (r.type, r.id), user=u, method='DELETE', status=tu.STATUS_OK)
        self.assertContainsNone(RepositoryDatabase, RepositoryDatabase.id == r.id)

    """
    VALIDATORS
    """
    def test_get_validator(self):
        params = RepositoryGetValidator.parse({'user_id': 1})
        with self.assertRaises(Invalid):
            params = RepositoryGetValidator.parse({'user_id': -2})
        with self.assertRaises(Invalid):
            params = RepositoryGetValidator.parse({})

    def test_add_validator(self):
        params = RepositoryAddValidator.parse({'user_id': 1, 'server_group_id': 1, 'name': 'testRepository', 'type': 'svn'})
        params = RepositoryAddValidator.parse({'user_id': 1, 'server_group_id': 1, 'name': 'testRepository', 'type': 'git'})

        with self.assertRaises(Invalid):
            params = RepositoryAddValidator.parse({'user_id': 1, 'server_group_id': 1, 'name': 'testRepository', 'type': 'spudro'})
        with self.assertRaises(Invalid):
            params = RepositoryAddValidator.parse({'user_id': 1, 'server_group_id': 1, 'name': 'testRepository'})
        with self.assertRaises(Invalid):
            params = RepositoryAddValidator.parse({'user_id': 1, 'name': 'testRepository', 'type': 'svn'})
        with self.assertRaises(Invalid):
            params = RepositoryAddValidator.parse({'user_id': 1, 'server_group_id': 1, 'type': 'svn'})
        with self.assertRaises(Invalid):
            params = RepositoryAddValidator.parse({'server_group_id': 1, 'name': 'testRepository', 'type': 'svn'})
        with self.assertRaises(Invalid):
            params = RepositoryAddValidator.parse({'user_id': 1, 'server_group_id': 1, 'name': 'testRepository'})

if __name__ == "__main__":
    import unittest
    unittest.main()
