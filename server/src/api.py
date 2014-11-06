import os
import shutil
from flask import Flask, helpers, request, jsonify, session, redirect

app = Flask(__name__)

from werkzeug import secure_filename
from generators.line import generatedata
import json
import traceback
import sys
from sim.dataio import loaddata, savedata, normalize_file, DATADIR
from sim.updatedata import updatedata
from sim.loadspreadsheet import loadspreadsheet
from sim.makeproject import makeproject
from sim.manualfit import manualfit
from sim.bunch import unbunchify
from sim.runsimulation import runsimulation
from sim.optimize import optimize
from optima.analysis import analysis
from optima.data import data
from optima.user import user
from optima.model import model
from optima.project import project
from optima.utils import allowed_file


UPLOAD_FOLDER = DATADIR #'/tmp/uploads' #todo configure


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DATABASE_URI'] = 'postgresql+psycopg2://postgres:root@localhost:5432/optima'

app.secret_key = 'F12Zr47j\3yX R~X@H!jmM]Lwf/,?KT'

app.register_blueprint(data, url_prefix = '/api/data')
app.register_blueprint(user, url_prefix = '/api/user')
app.register_blueprint(project, url_prefix = '/api/project')
app.register_blueprint(model, url_prefix = '/api/model')
app.register_blueprint(analysis, url_prefix = '/api/analysis')

""" site - needed to correctly redirect to it from blueprints """
@app.route('/')
def site():
    redirect('/')

""" API root, nothing interesting here """
@app.route('/api', methods=['GET'])
def root():
    return 'Optima API v.1.0.0'

if __name__ == '__main__':
    app.run(debug=True)
