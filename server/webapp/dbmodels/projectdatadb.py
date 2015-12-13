from flask_restful_swagger import swagger
from flask_restful import fields

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text
from sqlalchemy.orm import deferred

from server.webapp.dbconn import db
from server.webapp.fields import Uuid, LargeBinary


@swagger.model
class ProjectDataDb(db.Model):  # pylint: disable=R0903
    __tablename__ = 'project_data'
    resource_fields = {
        'id': Uuid,
        'meta': LargeBinary,
        'updated': fields.DateTime
    }
    id = db.Column(UUID(True), db.ForeignKey('projects.id'), primary_key=True)
    meta = deferred(db.Column(db.LargeBinary))
    updated = db.Column(
        db.DateTime(timezone=True), server_default=text('now()'))

    def __init__(self, project_id, meta, updated=None):
        self.id = project_id
        self.meta = meta
        self.updated = updated
