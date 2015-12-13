import dateutil
from datetime import datetime
from flask_restful_swagger import swagger
from flask_restful import fields

from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy import text

from server.webapp.dbconn import db
from server.webapp.fields import Uuid, Json, LargeBinary


@swagger.model
class ProjectDb(db.Model):
    __tablename__ = 'projects'
    resource_fields = {
        'id': Uuid,
        'name': fields.String,
        'datastart': fields.Integer,
        'dataend': fields.Integer,
        'populations': Json,
        'created': fields.DateTime,
        'updated': fields.DateTime,
        'version': fields.String,
        'settings': LargeBinary,
        'data': LargeBinary
    }
    id = db.Column(UUID(True), server_default=text(
        "uuid_generate_v1mc()"), primary_key=True)
    name = db.Column(db.String(60))
    user_id = db.Column(UUID(True), db.ForeignKey('users.id'))
    datastart = db.Column(db.Integer)
    dataend = db.Column(db.Integer)
    populations = db.Column(JSON)
    created = db.Column(
        db.DateTime(timezone=True), server_default=text('now()'))
    updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    version = db.Column(db.Text)
    settings = db.Column(db.LargeBinary)
    data = db.Column(db.LargeBinary)
    working_project = db.relationship('WorkingProjectDb', backref='projects',
                                      uselist=False)
    project_data = db.relationship('ProjectDataDb', backref='projects',
                                   uselist=False)
    parsets = db.relationship('ParsetsDb', backref='projects')
    results = db.relationship('ResultsDb', backref='results')

    def __init__(self, name, user_id, datastart, dataend, populations, version,
                 created=None, updated=None, settings=None, data=None,
                 parsets=None, results=None):  # pylint: disable=R0913
        self.name = name
        self.user_id = user_id
        self.datastart = datastart
        self.dataend = dataend
        self.populations = populations
        if created:
            self.created = created
        if updated:
            self.updated = updated
        self.version = version
        self.settings = settings
        self.data = data
        self.parsets = parsets or []
        self.results = results or []

    def has_data(self):
        return self.data is not None

    def has_model_parameters(self):
        return self.parsets is not None

    def data_upload_time(self):
        return self.project_data.updated if self.project_data else None

    def hydrate(self):
        from optima.project import Project
        from optima.utils import loads
        project_entry = Project()
        project_entry.uuid = self.id
        project_entry.name = self.name
        project_entry.created = (
            self.created or datetime.now(dateutil.tz.tzutc()))
        project_entry.modified = self.updated
        if self.data:
            project_entry.data = loads(self.data)
        if self.settings:
            project_entry.settings = loads(self.settings)
        if self.parsets:
            for parset_record in self.parsets:
                parset_entry = parset_record.hydrate()
                project_entry.addparset(parset_entry.name, parset_entry)
        return project_entry

    def restore(self, project):

        from datetime import datetime
        import dateutil
        from optima.utils import saves

        self.name = project.name
        self.created = project.created
        self.updated = datetime.now(dateutil.tz.tzutc())
        self.settings = saves(project.settings)
        self.data = saves(project.data)
        if project.parsets:
            from server.webapp.utils import update_or_create_parset
            for name, parset in project.parsets.iteritems():
                update_or_create_parset(self.id, name, parset)
