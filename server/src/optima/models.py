from api import db
from sqlalchemy import Column, Integer, String

class UserDb(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60))
    email = db.Column(db.String(200))
    openid = db.Column(db.String(200))

    def __init__(self, name, email, openid):
        self.name = name
        self.email = email
        self.openid = openid
