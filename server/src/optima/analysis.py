import os
import shutil
from flask import Flask, Blueprint, helpers, request, jsonify, session, redirect
from werkzeug import secure_filename
from generators.line import generatedata
import json
import traceback
import sys
from sim.dataio import loaddata, savedata, normalize_file, DATADIR
from sim.optimize import optimize

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
def runOptimisation():
    # should call method in optimize.py but it's not implemented yet. for now just returns back the file
    json_file = os.path.join(analysis.config['UPLOAD_FOLDER'], "optimisation.json")
    if (not os.path.exists(json_file)):
        return json.dumps({"status":"NOK", "reason":"Define the optimisation objectives first"})
    with open(json_file, 'r') as infile:
        data = json.load(infile)
    (lineplot, dataplot) = optimize()
    (lineplot, dataplot) = (unbunchify(lineplot), unbunchify(dataplot))
    return json.dumps({"lineplot":lineplot, "dataplot":dataplot})

