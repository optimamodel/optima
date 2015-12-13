from flask_restful_swagger import swagger
from flask_restful import fields
from sqlalchemy.dialects.postgresql import UUID
from server.webapp.dbconn import db
from server.webapp.fields import Uuid, LargeBinary


@swagger.model
class WorkingProjectDb(db.Model):  # pylint: disable=R0903
    __tablename__ = 'working_projects'
    resource_fields = {
        'id': Uuid,
        'is_working': fields.Boolean,
        'work_type': fields.String,
        'project': LargeBinary,
        'work_log_id': Uuid
    }
    id = db.Column(UUID(True), db.ForeignKey('projects.id'), primary_key=True)
    is_working = db.Column(db.Boolean, unique=False, default=False)
    work_type = db.Column(db.String(32), default=None)
    project = db.Column(db.LargeBinary)
    work_log_id = db.Column(UUID(True), default=None)

    def __init__(self, project_id, is_working=False, project=None,
                 work_type=None, work_log_id=None):  # pylint: disable=R0913
        self.id = project_id
        self.project = project
        self.is_working = is_working
        self.work_type = work_type
        self.work_log_id = work_log_id
