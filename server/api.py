from flask import Flask, redirect
from flask.ext.sqlalchemy import SQLAlchemy
import json
import os
import sys
import logging
from logging.handlers import SysLogHandler

app = Flask(__name__)
app.config.from_object('config')

if os.environ.get('OPTIMA_TEST_CFG'):
    app.config.from_envvar('OPTIMA_TEST_CFG')

if __package__ is None:
    import sys
    from os import path
    new_path = path.dirname( path.dirname( path.abspath(__file__) ) ) 
    print "appending to sys.path: %s" % new_path
    sys.path.append( new_path)
else:
    print "__package__", __package__

from optima.optima import Project

import server.webapp.dbconn
server.webapp.dbconn.db = SQLAlchemy(app)

from server.webapp.scenarios import scenarios
from server.webapp.model import model
from server.webapp.user import user
from server.webapp.project import project
from server.webapp.optimization import optimization

app.register_blueprint(user, url_prefix = '/api/user')
app.register_blueprint(project, url_prefix = '/api/project')
app.register_blueprint(model, url_prefix = '/api/model')
app.register_blueprint(scenarios, url_prefix = '/api/analysis/scenarios')
app.register_blueprint(optimization, url_prefix = '/api/analysis/optimization')


""" site - needed to correctly redirect to it from blueprints """
@app.route('/')
def site():
    redirect('/')
    return "OK"

""" API root, nothing interesting here """
@app.route('/api', methods=['GET'])
def root():
    return 'Optima API v.1.0.0'

def init_db():
    server.webapp.dbconn.db.create_all()

def init_logger():
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    init_logger()
    init_db()
    app.run(threaded=True, debug=True)
else:
    init_logger()
    init_db()
