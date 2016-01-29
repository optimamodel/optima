import json
import os
import sys
import logging

from flask import Flask, redirect, Blueprint, g, session, make_response

from flask_restful import Api
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask_restful_swagger import swagger

new_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if new_path not in sys.path:
    print "appending to sys.path: %s" % new_path
    sys.path.append(new_path)

import server.webapp.dbconn

app = Flask(__name__)
app.config.from_pyfile('config.py')

if os.environ.get('OPTIMA_TEST_CFG'):
    app.config.from_envvar('OPTIMA_TEST_CFG')

api_bp = Blueprint('api', __name__, static_folder='static')
api = swagger.docs(Api(api_bp), apiVersion='2.0')

server.webapp.dbconn.db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

from server.webapp.utils import init_login_manager
init_login_manager(login_manager)

from server.webapp.jsonhelper import OptimaJSONEncoder


@api.representation('application/json')
def output_json(data, code, headers=None):
    inner = json.dumps(data, cls=OptimaJSONEncoder)
    resp = make_response(inner, code)
    resp.headers.extend(headers or {})
    return resp


@api_bp.before_request
def before_request():
    from server.webapp.dbconn import db
    from server.webapp.dbmodels import UserDb
    db.engine.dispose()
    g.user = None
    if 'user_id' in session:
        g.user = UserDb.query.filter_by(id=session['user_id']).first()


from server.webapp.scenarios import scenarios
from server.webapp.model import model
from server.webapp.optimization import optimization
from server.webapp.resources.user import (User, UserDetail, CurrentUser,
                                          UserLogin, UserLogout)
from server.webapp.resources.project import (Projects, ProjectsAll, Project,
                                             ProjectCopy, ProjectSpreadsheet,
                                             ProjectData, ProjectFromData, Portfolio,
                                             Defaults)
from server.webapp.resources.project_constants import Parameters, Populations
from server.webapp.resources.project_progsets import Progsets, Progset, ProgsetData
from server.webapp.resources.project_parsets import Parsets, ParsetsData, ParsetsDetail, ParsetsCalibration
from server.webapp.resources.project_progsets import Programs, CostCoverage, CostCoverageGraph


app.register_blueprint(model, url_prefix='/api/model')
app.register_blueprint(scenarios, url_prefix='/api/analysis/scenarios')
app.register_blueprint(optimization, url_prefix='/api/analysis/optimization')

api.add_resource(User, '/api/user')
api.add_resource(UserDetail, '/api/user/<uuid:user_id>')
api.add_resource(CurrentUser, '/api/user/current')
api.add_resource(UserLogin, '/api/user/login')
api.add_resource(UserLogout, '/api/user/logout')

api.add_resource(Projects, '/api/project')
api.add_resource(ProjectsAll, '/api/project/all')
api.add_resource(Project, '/api/project/<uuid:project_id>')
api.add_resource(ProjectCopy, '/api/project/<uuid:project_id>/copy')
api.add_resource(ProjectFromData, '/api/project/data')
api.add_resource(ProjectData, '/api/project/<uuid:project_id>/data')
api.add_resource(ProjectSpreadsheet, '/api/project/<uuid:project_id>/spreadsheet')
api.add_resource(Progsets, '/api/project/<uuid:project_id>/progsets')
api.add_resource(Progset, '/api/project/<uuid:project_id>/progsets/<uuid:progset_id>')
api.add_resource(Programs, '/api/project/<uuid:project_id>/progsets/<uuid:progset_id>/programs')
api.add_resource(CostCoverage, '/api/project/<uuid:project_id>/progsets/<uuid:progset_id>/programs/<uuid:program_id>/costcoverage')
api.add_resource(CostCoverageGraph, '/api/project/<uuid:project_id>/progsets/<uuid:progset_id>/programs/<uuid:program_id>/costcoverage/graph')
api.add_resource(ProgsetData, '/api/project/<uuid:project_id>/progsets/<uuid:progset_id>/data')
api.add_resource(Portfolio, '/api/project/portfolio')
api.add_resource(Parameters, '/api/project/<project_id>/parameters')
api.add_resource(Populations, '/api/project/populations')
api.add_resource(Defaults, '/api/project/<uuid:project_id>/defaults')

api.add_resource(Parsets, '/api/project/<uuid:project_id>/parsets')
api.add_resource(ParsetsDetail, '/api/project/<uuid:project_id>/parsets/<uuid:parset_id>')
api.add_resource(ParsetsCalibration, '/api/parset/<uuid:parset_id>/calibration')
api.add_resource(ParsetsData, '/api/project/<uuid:project_id>/parsets/<uuid:parset_id>/data')
app.register_blueprint(api_bp, url_prefix='')


@app.route('/')
def site():
    """ site - needed to correctly redirect to it from blueprints """
    redirect('/')
    return "OK"


@app.route('/api', methods=['GET'])
def root():
    """ API root, nothing interesting here """
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
    app.run(threaded=True, debug=True, use_debugger=False)
else:
    init_logger()
    init_db()
