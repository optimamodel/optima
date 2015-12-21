import factory
import hashlib

from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory

from server.webapp.dbmodels import ParsetsDb
from server.webapp.dbmodels import ProgramsDb
from server.webapp.dbmodels import ProjectDataDb
from server.webapp.dbmodels import ProjectDb, ProgsetsDb
from server.webapp.dbmodels import ResultsDb
from server.webapp.dbmodels import UserDb
from server.webapp.dbmodels import WorkLogDb
from server.webapp.dbmodels import WorkingProjectDb

# from sqlalchemy import create_engine
# from sqlalchemy.orm import scoped_session, sessionmaker

# engine = create_engine('postgresql+psycopg2://test:test@localhost:5432/optima_test')
# session = scoped_session(sessionmaker(bind=engine))


# class BaseFactory(SQLAlchemyModelFactory):
#     class Meta:
#         sqlalchemy_session = session


class UserFactory(SQLAlchemyModelFactory):

    class Meta:
        model = UserDb

    name = factory.Faker('name')
    username = Sequence(lambda n: 'user_{}'.format(n))
    email = Sequence(lambda n: 'user_{}@test.com'.format(n))
    password = hashlib.sha224("test").hexdigest()
    is_admin = False


class ProjectFactory(SQLAlchemyModelFactory):

    class Meta:
        model = ProjectDb

    name = factory.Faker('name')
    user = factory.SubFactory(UserFactory)
    datastart = 2000
    dataend = 2030
    populations = [{"name": "Female sex workers", "short_name": "FSW", "sexworker": True, "injects": False, "sexmen": True, "client": False, "female": True, "male": False, "sexwomen": False}, \
            {"name": "Clients of sex workers", "short_name": "Clients", "sexworker": False, "injects": False, "sexmen": False, "client": True, "female": False, "male": True, "sexwomen": True}, \
            {"name": "Men who have sex with men", "short_name": "MSM", "sexworker": False, "injects": False, "sexmen": True, "client": False, "female": False, "male": True, "sexwomen": False}, \
            {"name": "Males who inject drugs", "short_name": "Male PWID", "sexworker": False, "injects": True, "sexmen": False, "client": False, "female": False, "male": True, "sexwomen": True}, \
            {"name": "Other males [enter age]", "short_name": "Other males", "sexworker": False, "injects": False, "sexmen": False, "client": False, "female": False, "male": True, "sexwomen": True}, \
            {"name": "Other females [enter age]", "short_name": "Other females", "sexworker": False, "injects": False, "sexmen": True, "client": False, "female": True, "male": False, "sexwomen": False}]
    version = '2.0'


class ParsetFactory(SQLAlchemyModelFactory):

    class Meta:
        model = ParsetsDb

    project = factory.SubFactory(ProjectFactory)
    name = factory.Faker('name')


class ResultFactory(SQLAlchemyModelFactory):

    class Meta:
        model = ResultsDb

    parset = factory.SubFactory(ParsetFactory)
    project = factory.SubFactory(ProjectFactory)
    calculation_type = 'simulation'


class WorkingProjectFactory(SQLAlchemyModelFactory):

    class Meta:
        model = WorkingProjectDb
    project = factory.SubFactory(ProjectFactory)


class WorkLogFactory(SQLAlchemyModelFactory):

    class Meta:
        model = WorkLogDb

    project = factory.SubFactory(ProjectFactory)


class ProjectDataFactory(SQLAlchemyModelFactory):

    class Meta:
        model = ProjectDataDb

    project = factory.SubFactory(ProjectFactory)


class ProgsetsFactory(SQLAlchemyModelFactory):

    class Meta:
        model = ProgsetsDb
    project = factory.SubFactory(ProjectFactory)
    name = factory.Faker('name')


class ProgramsFactory(SQLAlchemyModelFactory):

    class Meta:
        model = ProgramsDb

    progset = factory.SubFactory(ProgsetsFactory)
    project = factory.SubFactory(ProjectDataFactory)
    category = 'test'
    name = factory.Faker('name')
    short_name = factory.Faker('name')
    active = True
