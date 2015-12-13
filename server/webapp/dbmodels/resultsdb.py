from flask_restful_swagger import swagger
from flask_restful import fields

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text

from server.webapp.dbconn import db
from server.webapp.fields import Uuid, LargeBinary


@swagger.model
class ResultsDb(db.Model):
    __tablename__ = 'results'
    resource_fields = {
        'id': Uuid,
        'parset_id': Uuid,
        'project_id': Uuid,
        'calculation_type': fields.String,
        'blob': LargeBinary
    }
    id = db.Column(UUID(True), server_default=text(
        "uuid_generate_v1mc()"), primary_key=True)
    parset_id = db.Column(UUID(True), db.ForeignKey('parsets.id'))
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    calculation_type = db.Column(db.Text)
    blob = db.Column(db.LargeBinary)

    def __init__(self, parset_id, project_id, calculation_type, blob, id=None):
        self.parset_id = parset_id
        self.project_id = project_id
        self.calculation_type = calculation_type
        self.blob = blob
        if id:
            self.id = id
