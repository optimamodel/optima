#!/bin/env python
# -*- coding: utf-8 -*-
from server.api import app, init_db
from server.webapp.dbconn import db
import unittest
import hashlib
import json
from sqlalchemy.engine import reflection
from sqlalchemy.schema import (
    MetaData,
    Table,
    DropTable,
    ForeignKeyConstraint,
    DropConstraint,
)
from server.tests.factories import (UserFactory, ProjectFactory, ParsetFactory,
                                    ProgsetsFactory, ProgramsFactory, make_password)


class OptimaTestCase(unittest.TestCase):
    """
    Baseclass for Optima API endpoint tests.

    This baseclass provides a setup that can be inherited to run API tests.

    Example:

        class SomeTestCase(OptimaTestCase):

            def setUp(self):
                super(SomeTestCase, self).setUp()

            def tearDown(self):
                super(SomeTestCase, self).tearDown()

            def test_a_response(self):
                response = self.test_client.get('/api/path')
                self.assertEqual(response.status_code, 200)


    """

    default_username = 'test'

    default_pops = [
        {"name": "Female sex workers", "short_name": "FSW", "sexworker": True, "injects": False,
         "sexmen": True, "client": False, "female": True, "male": False, "sexwomen": False},
        {"name": "Clients of sex workers", "short_name": "Clients", "sexworker": False, "injects": False,
         "sexmen": False, "client": True, "female": False, "male": True, "sexwomen": True},
        {"name": "Men who have sex with men", "short_name": "MSM", "sexworker": False, "injects": False,
         "sexmen": True, "client": False, "female": False, "male": True, "sexwomen": False},
        {"name": "Males who inject drugs", "short_name": "Male PWID", "sexworker": False, "injects": True,
         "sexmen": False, "client": False, "female": False, "male": True, "sexwomen": True},
        {"name": "Other males [enter age]", "short_name": "Other males", "sexworker": False, "injects": False,
         "sexmen": False, "client": False, "female": False, "male": True, "sexwomen": True},
        {"name": "Other females [enter age]", "short_name": "Other females", "sexworker": False, "injects": False,
         "sexmen": True, "client": False, "female": True, "male": False, "sexwomen": False}
    ]

    progset_test_data = {
        'name': 'Progset',
        'programs': [
            {
                'active': True,
                'category': 'Prevention',
                'name': 'Condom promotion and distribution',
                'parameters': [
                    {
                        'active': True,
                        'pops': ['MSM'],
                        'param': 'condcas'
                    },
                ],
                'short_name': 'Condoms',
                'criteria': {'hivstatus': 'allstates', 'pregnant': False},
            }, {
                'active': False,
                'category': 'Care and treatment',
                'name': 'Post-exposure prophylaxis',
                'parameters': [],
                "short_name": "PEP",
                'criteria': {'hivstatus': 'allstates', 'pregnant': False},
            },
        ],
    }

    def create_record_with(self, factory_class, **kwargs):
        factory_class._meta.sqlalchemy_session = self.session
        rv = factory_class.create(**kwargs)
        self.session.commit()
        return rv

    def create_user(self, username=default_username, **kwargs):
        kwargs['username'] = username
        return self.create_record_with(UserFactory, **kwargs)

    def get_any_user_id(self, admin=False):
        from server.webapp.dbmodels import UserDb
        user = UserDb.query.filter(UserDb.is_admin == admin).first()
        if user is None:
            return None
        return str(user.id)

    def get_user_id_by_email(self, email):
        from server.webapp.dbmodels import UserDb
        user = UserDb.query.filter(UserDb.email == email).first()
        return str(user.id)

    def create_project(self, return_instance=False, progsets_count=0,
                       programs_per_progset=2, parset_count=0, pars={},
                       **kwargs):
        if 'user_id' not in kwargs:
            kwargs['user_id'] = self.get_any_user_id()
        project = self.create_record_with(ProjectFactory, **kwargs)

        for x in range(progsets_count):
            progset = self.create_record_with(ProgsetsFactory, project_id=project.id)
            for y in range(programs_per_progset):
                self.create_record_with(
                    ProgramsFactory,
                    project_id=project.id,
                    progset_id=progset.id,
                    active=True,
                    pars=pars
                )
        for x in range(parset_count):
            self.create_record_with(ParsetFactory, project_id=project.id)

        if return_instance:
            return project
        return str(project.id)

    def api_create_project(self):
        project_data = json.dumps({
            'name': 'test',
            'datastart': 2000,
            'dataend': 2015,
            'populations': ProjectFactory.populations
        })
        headers = {'Content-Type': 'application/json'}
        response = self.client.post('/api/project', data=project_data, headers=headers)
        self.assertEqual(response.status_code, 201)
        return response

    def list_projects(self, user_id):
        from server.webapp.dbmodels import ProjectDb
        """ Helper method to list projects for the given user id"""
        projects = ProjectDb.query.filter_by(user_id=user_id).all()
        return [project for project in projects]

    def api_create_progset(self, project_id):
        headers = {'Content-Type': 'application/json'}
        response = self.client.post(
            '/api/project/{}/progsets'.format(project_id),
            data=json.dumps(self.progset_test_data),
            headers=headers
        )
        self.assertEqual(response.status_code, 201, response.data)

        response_data = json.loads(response.data)
        self.assertTrue('id' in response_data)
        progset_id = response_data['id']

        return progset_id

    def login(self, username=default_username, password=None):
        if not password:
            password = make_password()
        login_data = '{"username":"%s","password":"%s"}' % (username, password)
        response = self.client.post('/api/user/login', data=login_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        return response

    def logout(self):
        self.client.get('/api/user/logout', follow_redirects=True)

    def setUp(self):
        from sqlalchemy import orm
        self.test_password = hashlib.sha224("test").hexdigest()
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://test:test@localhost:5432/optima_test'
        app.config['TESTING'] = True
        print "app created %s" % app
        init_db()
        self.session = orm.scoped_session(orm.sessionmaker())
        self.session.configure(bind=db.engine)
        print("db created. db: %s" % db)
        self.client = app.test_client()

    def _db_DropEverything(self, db):
        # From http://www.sqlalchemy.org/trac/wiki/UsageRecipes/DropEverything

        conn = db.engine.connect()

        # the transaction only applies if the DB supports
        # transactional DDL, i.e. Postgresql, MS SQL Server
        trans = conn.begin()

        inspector = reflection.Inspector.from_engine(db.engine)

        # gather all data first before dropping anything.
        # some DBs lock after things have been dropped in
        # a transaction.
        metadata = MetaData()

        tbs = []
        all_fks = []

        for table_name in inspector.get_table_names():
            fks = []
            for fk in inspector.get_foreign_keys(table_name):
                if not fk['name']:
                    continue
                fks.append(
                    ForeignKeyConstraint((), (), name=fk['name'])
                )
            t = Table(table_name, metadata, *fks)
            tbs.append(t)
            all_fks.extend(fks)

        for fkc in all_fks:
            conn.execute(DropConstraint(fkc))

        for table in tbs:
            conn.execute(DropTable(table))

        trans.commit()

    def tearDown(self):
        self.logout()
        self.session.rollback()
        self.session.remove()
        self._db_DropEverything(db)
        db.drop_all()
        db.get_engine(app).dispose()
        print "db dropped"
