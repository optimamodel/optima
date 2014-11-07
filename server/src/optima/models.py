from api import db

class UserDb(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60))
    email = db.Column(db.String(200))
    openid = db.Column(db.String(200))
    projects = db.relationship('ProjectDb', backref='user',
                                lazy='dynamic')

    def __init__(self, name, email, openid):
        self.name = name
        self.email = email
        self.openid = openid

class ProjectDb(db.Model)
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    datastart = db.Column(db.DateTime)
    dataend = db.Column(db.DateTime)
    econ_datastart = db.Column(db.DateTime)
    econ_dataend = db.Column(db.DateTime)
    programs = db.Column(db.String(60))
    populations = db.Column(db.String(60))

    def __init__(self, name, email, openid):
        self.name = name
        self.email = email
        self.openid = openid
