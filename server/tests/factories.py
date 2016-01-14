import factory
import hashlib
from optima.utils import saves

from factory import Sequence, fuzzy
from factory.alchemy import SQLAlchemyModelFactory

from server.webapp.dbmodels import (ParsetsDb, ProgramsDb, ProjectDataDb,
                                    ProjectDb, ProgsetsDb, ResultsDb, UserDb,
                                    WorkLogDb, WorkingProjectDb)
from server.webapp.populations import populations


def make_password(password="test"):
    return hashlib.sha224("test").hexdigest()


def test_populations():
    pops = populations()
    for i in range(2):
        for j in range(len(pops)):
            pops[j]['active'] = True
    return pops


class UserFactory(SQLAlchemyModelFactory):

    class Meta:
        model = UserDb

    name = factory.Faker('name')
    username = Sequence(lambda n: 'user_{}'.format(n))
    email = Sequence(lambda n: 'user_{}@test.com'.format(n))
    password = make_password()
    is_admin = False


class ProjectFactory(SQLAlchemyModelFactory):

    class Meta:
        model = ProjectDb

    name = fuzzy.FuzzyText(prefix='project_')
    datastart = 2000
    dataend = 2030
    populations = test_populations()
    version = '{}'

    @factory.lazy_attribute
    def user_id(self):
        return UserDb.query.filter_by(is_admin=False).first().id


class ParsetFactory(SQLAlchemyModelFactory):

    class Meta:
        model = ParsetsDb

    name = factory.Faker('name')
    # pars = saves(parameter_list)


class ResultFactory(SQLAlchemyModelFactory):

    class Meta:
        model = ResultsDb

    parset = factory.SubFactory(ParsetFactory)
    project = factory.SubFactory(ProjectFactory)
    calculation_type = ResultsDb.CALIBRATION_TYPE


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

    name = fuzzy.FuzzyText(prefix='progset_')


class ProgramsFactory(SQLAlchemyModelFactory):

    class Meta:
        model = ProgramsDb

    category = 'Test category'
    name = fuzzy.FuzzyText(prefix='program_')
    short_name = fuzzy.FuzzyText()
    active = True
    criteria = {'hivstatus': 'allstates', 'pregnant': False}
