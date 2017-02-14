
import os
import sys
import logging

import redis

from flask import Flask, redirect, abort, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager

app = Flask(__name__)
app.config.from_pyfile('config.py')

import matplotlib
matplotlib.use(app.config["MATPLOTLIB_BACKEND"])

if os.environ.get('OPTIMA_TEST_CFG'):
    app.config.from_envvar('OPTIMA_TEST_CFG')

from server.webapp import dbconn
dbconn.db = SQLAlchemy(app)
dbconn.redis = redis.StrictRedis.from_url(app.config["REDIS_URL"])

from server.webapp.dbmodels import UserDb

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(userid):
    try:
        user = UserDb.query.filter_by(id=userid).first()
    except Exception:
        user = None
    return user


@login_manager.request_loader
def load_user_from_request(request):  # pylint: disable=redefined-outer-name

    # try to login using the secret url arg
    secret = request.args.get('secret')
    if secret:
        user = UserDb.query.filter_by(password=secret, is_admin=True).first()
        if user:
            return user

    # finally, return None if both methods did not login the user
    return None


@login_manager.unauthorized_handler
def unauthorized_handler():
    abort(401)


@app.route('/')
def site():
    """ site - needed to correctly redirect to it from blueprints """
    return redirect('/')


# NOTE: the twisted wgsi server is set up to
# only allows url's with /api/* to be served

@app.route('/api', methods=['GET'])
def root():
    """ API root, nothing interesting here """
    return 'Optima API v.1.0.0'


from .webapp.handlers import api_blueprint, get_post_data_json, report_exception_decorator, login_required
from .webapp import dataio


app.register_blueprint(api_blueprint, url_prefix='')


@app.route('/api/procedure', methods=['POST'])
@report_exception_decorator
@login_required
def run_remote_procedure():
    """
    url-args:
        'procedure': string name of function in dataio
        'args': list of arguments for the function
    """
    json = get_post_data_json()

    fn_name = json['name']
    print('>> Checking function "dataio.%s" -> %s' % (fn_name, hasattr(dataio, fn_name)))
    fn = getattr(dataio, fn_name)

    args = json.get('args', [])
    kwargs = json.get('kwargs', {})
    return jsonify(fn(*args, **kwargs))


from flask import helpers
@app.route('/api/download', methods=['POST'])
@report_exception_decorator
@login_required
def get_remote_file():
    """
    url-args:
        'procedure': string name of function in dataio
        'args': list of arguments for the function
    """
    json = get_post_data_json()

    fn_name = json['name']
    print('>> Checking function "dataio.%s" -> %s' % (fn_name, hasattr(dataio, fn_name)))
    fn = getattr(dataio, fn_name)

    args = json.get('args', [])
    kwargs = json.get('kwargs', {})
    full_filename = fn(*args, **kwargs)
    dirname, filename = os.path.split(full_filename)
    print(">> Get remote filen %s %s" % (dirname, filename))
    return helpers.send_from_directory(dirname, filename)


def init_db():
    print("Loading DB...")

    dbconn.db.engine.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    dbconn.db.create_all()

    # clear dangling tasks from the last session
    from server.webapp.dbmodels import WorkLogDb

    work_logs = dbconn.db.session.query(WorkLogDb)
    print "> Deleting dangling work_logs", work_logs.count()
    for work_log in work_logs:
        work_log.cleanup()
    work_logs.delete()

    dbconn.db.session.commit()


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
