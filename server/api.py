
import os
import sys
import logging
import matplotlib.pyplot as ppl
import redis

from flask import Flask, abort, jsonify, request, json, helpers
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.utils import secure_filename


# Create Flask app that does everything
app = Flask(__name__)

# Try to load the config file -- this often fails, so predefine a warning message
errormsg = 'Could not load Optima configuration file\n'
errormsg += 'Please ensure that you have copied server/config.example.py to server/config.py\n'
errormsg += 'Note that this is NOT done automatically'
try: # File exists
    app.config.from_pyfile('config.py')
except: # File doesn't exist
    raise Exception(errormsg)

# This might also fail if configuration is old or misspecified
try:
    ppl.switch_backend(app.config["MATPLOTLIB_BACKEND"])
except:
    raise Exception(errormsg)

if os.environ.get('OPTIMA_TEST_CFG'):
    app.config.from_envvar('OPTIMA_TEST_CFG')

# Import Optima for the first time, and print debugging info
import optima
optima.debuginfo()

# Load the database
from server.webapp import dbconn
import scirisweb as sw
dbconn.db = SQLAlchemy(app)
dbconn.datastore = sw.make_datastore(app.config["DATASTORE_URL"])

from server.webapp.dbmodels import UserDb

login_manager = LoginManager()
login_manager.init_app(app)


# attaches the function for the flask login user_loader
# thus making the login_user user object: an SQLAlchemy record
# for UserDb
@login_manager.user_loader
def load_user(userid):
    try:
        user = UserDb.query.filter_by(id=userid).first()
    except Exception:
        user = None
    return user


# decorator for the user requrest so that
# a secret url query can be used to by-pass the login
# process - not really used but left in as legacy
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


# NOTE: the twisted wgsi server is set up to
# only allows url's with /api/* to be served
@app.route('/api', methods=['GET'])
def root():
    """ API root, nothing interesting here """
    return 'Optima API v.1.0.0'


from .webapp.handlers import api_blueprint, get_post_data_json, report_exception_decorator, login_required
from .webapp import dataio
from .webapp.parse import normalize_obj


# this is used only to load the user-related url handlers
app.register_blueprint(api_blueprint, url_prefix='')


# Using the RPC approach, functions in the web-client are
# directly called using 
#
# - rpcService.rpcRun => run_remote_procedure
# - rpcService.rpcAsyncRun => run_remote_async_task
# - rpcService.rpcDownload => get_remote_file
# - rpcService.rpcUpload => receive_uploaded_file
#
# All rpcService functions are called with the signature:
#
#    rpcFunc('python_function', [arg0, arg1, arg2...], 
#         { kwarg0: val0, kwarg1: val1 ...})

# rpcRun will return a JSON dictionary, the target function
# will directly receive the args and kwargs, and return
# a JSON dictionary

# rpcRun will return a JSON dictionary, the target function
# will be from the tasks.py module. the target function
# will directly receive the args and kwargs, and return
# a JSON dictionary

# rpcDownload will receive and save a file on the client, the target function
# will directly receive the args and kwargs

# rpcUpload will send a file to the webserver, the target function
# will receive the filename of the saved file as the first arg, and
# the args from the function after, as well as kwargs

@app.route('/api/procedure', methods=['POST'])
@report_exception_decorator
@login_required
def run_remote_procedure():
    """
    url-args:
        'name': string name of function in dataio
        'args': list of arguments for the function
        'kwargs': dictionary of named parameters for the function
    """
    json = get_post_data_json()

    fn_name = json['name']
    print('>> Checking function "dataio.%s" -> %s' % (fn_name, hasattr(dataio, fn_name)))
    fn = getattr(dataio, fn_name)

    args = json.get('args', [])
    kwargs = json.get('kwargs', {})
    result = fn(*args, **kwargs)
    if result is None:
        result = ''
    else:
        result = jsonify(normalize_obj(result))
    return result


@app.route('/api/task', methods=['POST'])
@report_exception_decorator
@login_required
def run_remote_async_task():
    """
    url-args:
        'name': string name of function in dataio
        'args': list of arguments for the function
        'kwargs': dictionary of named parameters for the function
    """
    json = get_post_data_json()
    import server.webapp.tasks as tasks

    fn_name = json['name']
    print('>> Checking function "dataio.%s" -> %s' % (fn_name, hasattr(dataio, fn_name)))
    fn = getattr(tasks, fn_name)

    args = json.get('args', [])
    kwargs = json.get('kwargs', {})
    result = fn(*args, **kwargs)
    if result is None:
        result = ''
    else:
        result = jsonify(normalize_obj(result))
    return result


@app.route('/api/download', methods=['POST'])
@report_exception_decorator
@login_required
def get_remote_file():
    """
    url-args:
        'name': string name of function in dataio
        'args': list of arguments for the function
        'kwargs': dictionary of named parameters for the function
    """
    json = get_post_data_json()

    fn_name = json['name']
    print('>> Checking function "dataio.%s" -> %s' % (fn_name, hasattr(dataio, fn_name)))
    fn = getattr(dataio, fn_name)

    args = json.get('args', [])
    kwargs = json.get('kwargs', {})

    # BUG: exceptions in get_remote_file are caught and
    # transformed into a json string with the stack trace
    # however the client is unable to pick it up
    # haven't found the bug yet, but it may have something
    # to do the with the POST handler expecting responsearray

    full_filename = fn(*args, **kwargs)

    dirname, filename = os.path.split(full_filename)

    response = helpers.send_from_directory(
        dirname,
        filename,
        as_attachment=True,
        attachment_filename=filename)
    response.status_code = 201
    response.headers["filename"] = filename

    return response


@app.route('/api/upload', methods=['POST'])
@report_exception_decorator
def receive_uploaded_file():
    """
    url-args:
        'name': string name of function in dataio
        'args': list of arguments for the function
        'kwargs': dictionary of named parameters for the function
    """
    file = request.files['file']
    filename = secure_filename(file.filename)
    dirname = app.config['UPLOAD_FOLDER']
    if not (os.path.exists(dirname)):
        os.makedirs(dirname)
    uploaded_fname = os.path.join(dirname, filename)
    file.save(uploaded_fname)
    print("> receive_uploaded_file save %s" % (uploaded_fname))

    fn_name = request.form.get('name')
    args = json.loads(request.form.get('args', "[]"))
    kwargs = json.loads(request.form.get('kwargs', "{}"))
    args.insert(0, uploaded_fname)

    fn = getattr(dataio, fn_name)
    print("> receive_uploaded_file %s '%s'" % (fn_name, args))
    result = fn(*args, **kwargs)

    if result is None:
        return ''
    else:
        return jsonify(normalize_obj(result))


def init_db():
    print("Loading DB...")

    dbconn.db.engine.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    dbconn.db.create_all()

    # clear dangling tasks from the last session
    # from server.webapp.dbmodels import WorkLogDb
    # work_logs = dbconn.db.session.query(WorkLogDb)
    # print("> Deleting dangling work_logs", work_logs.count())
    # work_logs.delete()

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
