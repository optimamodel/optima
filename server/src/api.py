import os
import shutil
from flask import Flask, helpers, request, jsonify, session, redirect, abort
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug import secure_filename
from generators.line import generatedata
import json
import traceback
import sys
from sim.dataio import loaddata, savedata, DATADIR
import optima.dbconn

app = Flask(__name__)

UPLOAD_FOLDER = DATADIR #'/tmp/uploads' #todo configure

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://optima:optima@localhost:5432/optima'

optima.dbconn.db = SQLAlchemy(app)

from sim.updatedata import updatedata
from sim.loadspreadsheet import loadspreadsheet
from sim.makeproject import makeproject
from sim.manualfit import manualfit
from sim.bunch import unbunchify
from sim.runsimulation import runsimulation
from sim.optimize import optimize
from optima.analysis import analysis
from optima.data import data
from optima.model import model
from optima.user import user
from optima.project import project
from optima.utils import allowed_file

app.secret_key = 'F12Zr47j\3yX R~X@H!jmM]Lwf/,?KT'

app.register_blueprint(data, url_prefix = '/api/data')
app.register_blueprint(user, url_prefix = '/api/user')
app.register_blueprint(project, url_prefix = '/api/project')
app.register_blueprint(model, url_prefix = '/api/model')
app.register_blueprint(analysis, url_prefix = '/api/analysis')

# Execute this method after every request.
# Check response and return exception if status is not OK.
@app.after_request
def check_response_for_errors(response):
    responseJS = None
    try:
        # Load JSON from string
        responseJS = json.loads( response.get_data() )
    except :
        pass
    
    # Make sure the response status was OK. Response body is javascript that is successfully
    # parsed. And status in JSON is NOK implying there was an error.
    if response.status_code == 200 and responseJS is not None and 'status' in responseJS and responseJS['status'] == "NOK":
        response.status_code = 500
    
    return response


""" site - needed to correctly redirect to it from blueprints """
@app.route('/')
def site():
    redirect('/')

""" API root, nothing interesting here """
@app.route('/api', methods=['GET'])
def root():
    return 'Optima API v.1.0.0'

def init_db():
    optima.dbconn.db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
