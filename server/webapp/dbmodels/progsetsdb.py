from flask_restful_swagger import swagger
from flask_restful import fields

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text

from server.webapp.dbconn import db
from server.webapp.fields import Uuid


@swagger.model
class ProgsetsDb(db.Model):

    __tablename__ = 'progsets'
    resource_fields = {
        'id': Uuid,
        'project_id': Uuid,
        'name': fields.String,
        'created': fields.DateTime,
        'updated': fields.DateTime
    }

    id = db.Column(UUID(True), server_default=text(
        "uuid_generate_v1mc()"), primary_key=True)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    name = db.Column(db.String)
    created = db.Column(
        db.DateTime(timezone=True), server_default=text('now()'))
    updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    programs = db.relationship('ProgramsDb', backref='programs', lazy='joined')

    def __init__(self, project_id, name, created=None, updated=None, id=None):
        self.project_id = project_id
        self.name = name
        if created:
            self.created = created
        if updated:
            self.updated = updated
        if id:
            self.id = id

    def hydrate(self):
        from optima.programs import Programset
        progset_entry = Programset(
            name=self.name,
            programs=None
        )

        return progset_entry
