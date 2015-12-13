from flask_restful_swagger import swagger
from flask_restful import fields

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text

from server.webapp.dbconn import db
from server.webapp.fields import Uuid


@swagger.model
class WorkLogDb(db.Model):  # pylint: disable=R0903
    __tablename__ = "work_log"
    resource_fields = {
        'id': Uuid,
        'work_type': fields.String,
        'project_id': Uuid,
        'start_time': fields.DateTime,
        'stop_time': fields.DateTime,
        'status': fields.String,
        'error': fields.String
    }
    work_status = db.Enum(
        'started', 'completed', 'cancelled', 'error', name='work_status')

    id = db.Column(UUID(True), primary_key=True)
    work_type = db.Column(db.String(32), default=None)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    start_time = db.Column(
        db.DateTime(timezone=True), server_default=text('now()'))
    stop_time = db.Column(db.DateTime(timezone=True), default=None)
    status = db.Column(work_status, default='started')
    error = db.Column(db.Text, default=None)

    def __init__(self, project_id, work_type=None):
        self.project_id = project_id
        self.work_type = work_type
