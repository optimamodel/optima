from flask import Flask, redirect
from flask.ext.sqlalchemy import SQLAlchemy
import json
from src.sim.dataio import DATADIR
import optima.dbconn
import os
import sys
import logging
from logging.handlers import SysLogHandler

app = Flask(__name__)

app.config.from_object('config')
app.config['UPLOAD_FOLDER'] = DATADIR
if os.environ.get('OPTIMA_TEST_CFG'):
    app.config.from_envvar('OPTIMA_TEST_CFG')

optima.dbconn.db = SQLAlchemy(app)

from optima.scenarios import scenarios
from optima.data import data
from optima.model import model
from optima.user import user
from optima.project import project
from optima.optimization import optimization

app.register_blueprint(data, url_prefix = '/api/data')
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
    optima.dbconn.db.create_all()

def init_logger():
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    init_logger()
    init_db()
    app.run(threaded=True, debug=True)
else:
    init_logger()
    init_db()
