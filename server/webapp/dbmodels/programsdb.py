from flask_restful_swagger import swagger
from flask_restful import fields

from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import text

from server.webapp.dbconn import db
from server.webapp.fields import Uuid, Json


@swagger.model
class ProgramsDb(db.Model):

    __tablename__ = 'programs'
    resource_fields = {
        'id': Uuid,
        'progset_id': Uuid,
        'project_id': Uuid,
        'category': fields.String,
        'name': fields.String,
        'short_name': fields.String,
        'pars': Json,
        'active': fields.Boolean,
        'created': fields.DateTime,
        'updated': fields.DateTime
    }

    id = db.Column(UUID(True), server_default=text(
        "uuid_generate_v1mc()"), primary_key=True)
    progset_id = db.Column(UUID(True), db.ForeignKey('progsets.id'))
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    category = db.Column(db.String)
    name = db.Column(db.String)
    short_name = db.Column(db.String)
    pars = db.Column(JSON)
    active = db.Column(db.Boolean)
    created = db.Column(
        db.DateTime(timezone=True), server_default=text('now()'))
    updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())

    def __init__(self, project_id, progset_id, name,
                 short_name, category, active=False, pars=None,
                 created=None, updated=None, id=None):

        self.project_id = project_id
        self.progset_id = progset_id
        self.name = name
        self.short_name = short_name
        self.category = category
        self.pars = pars
        self.active = active
        if created:
            self.created = created
        if updated:
            self.updated = updated
        if id:
            self.id = id
