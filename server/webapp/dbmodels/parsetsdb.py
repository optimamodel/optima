from flask_restful_swagger import swagger
from flask_restful import fields

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text

from server.webapp.dbconn import db
from server.webapp.fields import Uuid, LargeBinary


@swagger.model
class ParsetsDb(db.Model):
    __tablename__ = 'parsets'
    resource_fields = {
        'id': Uuid,
        'project_id': Uuid,
        'name': fields.String,
        'created': fields.DateTime,
        'updated': fields.DateTime,
        'pars': LargeBinary
    }
    id = db.Column(UUID(True), server_default=text(
        "uuid_generate_v1mc()"), primary_key=True)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    name = db.Column(db.Text)
    created = db.Column(
        db.DateTime(timezone=True), server_default=text('now()'))
    updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    pars = db.Column(db.LargeBinary)

    def __init__(self, project_id, name, created=None,
                 updated=None, pars=None, id=None):
        self.project_id = project_id
        self.name = name
        if created:
            self.created = created
        if updated:
            self.updated = updated
        self.pars = pars
        if id:
            self.id = id

    def hydrate(self):
        from optima.parameters import Parameterset
        from optima.utils import loads
        parset_entry = Parameterset()
        parset_entry.name = self.name
        parset_entry.uuid = self.id
        parset_entry.created = self.created
        parset_entry.modified = self.updated
        parset_entry.pars = loads(self.pars)
        return parset_entry
