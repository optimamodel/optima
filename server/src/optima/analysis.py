import os
import shutil
from flask import Flask, Blueprint, helpers, request, jsonify, session, redirect
from werkzeug import secure_filename
from generators.line import generatedata
import json
import traceback
import sys
from sim.dataio import loaddata, savedata, DATADIR
from sim.optimize import optimize
from utils import loaddir
from flask.ext.login import login_required

""" route prefix: /api/analysis """
analysis = Blueprint('analysis',  __name__, static_folder = '../static')
analysis.config = {}

@analysis.record
def record_params(setup_state):
  app = setup_state.app
  analysis.config = dict([(key,value) for (key,value) in app.config.iteritems()])

"""
Defines optimisation objectives from the data collected on the frontend.
"""
@analysis.route('/optimisation/define/<defineType>', methods=['POST'])
@login_required
def defineObjectives(defineType):
    data = json.loads(request.data)
    json_file = os.path.join(analysis.config['UPLOAD_FOLDER'], "optimisation.json")
    with open(json_file, 'w') as outfile:
        json.dump(data, outfile)
    return json.dumps({'status':'OK'})

"""
Starts optimisation for the current model. Gives back line plot and two pie plots.
"""
@analysis.route('/optimisation/start')
@login_required
def runOptimisation():
    # should call method in optimize.py but it's not implemented yet. for now just returns back the file
    reply = {'status':'NOK'}
    project_name = session.get('project_name', '')
    if project_name == '':
        reply['reason'] = 'No project is open'
        return jsonify(reply)

    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % project_name
        return jsonify(reply)
    file_name = helpers.safe_join(PROJECTDIR, project_name+'.prj')
    print("project file_name: %s" % file_name)
    json_file = os.path.join(analysis.config['UPLOAD_FOLDER'], "optimisation.json")
    if (not os.path.exists(json_file)):
        reply["reason"] = "Define the optimisation objectives first"
        return jsonify(reply)
    (lineplot, dataplot) = optimize(project_name)
    (lineplot, dataplot) = (unbunchify(lineplot), unbunchify(dataplot))
    return json.dumps({"lineplot":lineplot, "dataplot":dataplot})

