import hashlib

from factory.alchemy import SQLAlchemyModelFactory
from factory import Sequence

from server.webapp.dbmodels import UserDb


class UserFactory(SQLAlchemyModelFactory):

    class Meta:
        model = UserDb

    name = 'test'
    email = Sequence(lambda n: 'user_{}@test.com'.format(n))
    password = hashlib.sha224("test").hexdigest()
    is_admin = False
