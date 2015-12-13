from flask_restful_swagger import swagger
from flask_restful import fields

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text

from server.webapp.dbconn import db
from server.webapp.fields import Uuid


@swagger.model
class UserDb(db.Model):

    __tablename__ = 'users'

    resource_fields = {
        'id': Uuid,
        'name': fields.String,
        'email': fields.String,
        'is_admin': fields.Boolean,
    }

    id = db.Column(UUID(True), server_default=text(
        "uuid_generate_v1mc()"), primary_key=True)
    name = db.Column(db.String(60))
    email = db.Column(db.String(200))
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, server_default=text('FALSE'))
    projects = db.relationship('ProjectDb', backref='users',
                               lazy='dynamic')

    def __init__(self, name, email, password, is_admin=False):
        self.name = name
        self.email = email
        self.password = password
        self.is_admin = is_admin

    def get_id(self):
        return self.id

    def is_active(self):  # pylint: disable=R0201
        return True

    def is_anonymous(self):  # pylint: disable=R0201
        return False

    def is_authenticated(self):  # pylint: disable=R0201
        return True
