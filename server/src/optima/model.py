import os
import shutil
from flask import Flask, Blueprint, helpers, request, jsonify, session, redirect
from werkzeug import secure_filename
from generators.line import generatedata
import json
import traceback
import sys
from sim.dataio import loaddata, savedata, DATADIR
from sim.updatedata import updatedata
from sim.loadspreadsheet import loadspreadsheet
from sim.makeproject import makeproject
from sim.manualfit import manualfit
from sim.autofit import autofit
from sim.bunch import unbunchify
from sim.runsimulation import runsimulation
from sim.optimize import optimize
from utils import loaddir

""" route prefix: /api/model """
model = Blueprint('model',  __name__, static_folder = '../static')
model.config = {}

@model.record
def record_params(setup_state):
  app = setup_state.app
  model.config = dict([(key,value) for (key,value) in app.config.iteritems()])


""" 
Uses provided parameters to manually calibrate the model (update it with these data) 
TODO: do it with the project which is currently in scope
"""
@model.route('/calibrate/auto', methods=['POST'])
def doAutoCalibration():
    reply = {'status':'NOK'}
    print('data: %s' % request.data)
    data = json.loads(request.data)
    project_name = session.get('project_name', '')
    if project_name == '':
        reply['reason'] = 'No project is open'
        return jsonify(reply)

    file_name = helpers.safe_join(loaddir(model), project_name+'.prj')
    print("project file_name: %s" % file_name)
    if not os.path.exists(file_name):
        reply['reason'] = 'File for project %s does not exist' % project_name
        return jsonify(reply)

    fits = autofit(file_name, data)
    print("fits: %s" % fits)
    fits = [unbunchify(x) for x in fits]
    print("unbunchified fits: %s" % fits)
    return jsonify(fits[0])


""" 
Uses provided parameters to manually calibrate the model (update it with these data) 
TODO: do it with the project which is currently in scope
"""
@model.route('/calibrate/manual', methods=['POST'])
def doManualCalibration():
    data = json.loads(request.data)
    project_name = session.get('project_name', '')
    if project_name == '':
        return jsonify({'status':'NOK', 'reason':'no project is open'})

    file_name = helpers.safe_join(loaddir(model), project_name+'.prj')
    print("project file_name: %s" % file_name)
    if not os.path.exists(file_name):
        reply['reason'] = 'File for project %s does not exist' % project_name

    D = manualfit(file_name, data)
    print("D: %s" % D)
    fits = {} #todo: how to get graphs from the model after calibration? @cliffkerr ?
    return jsonify(fits[0])


"""
Starts simulation for the given project and given date range. 
Returns back the file with the simulation data. (?) #FIXME find out how to use it
"""
@model.route('/view', methods=['POST'])
def doRunSimulation():
    data = json.loads(request.data)
    project_name = session.get('project_name', '')
    if project_name == '':
        return jsonify({'status':'NOK', 'reason':'no project is open'})

    #expects json: {"startyear":year,"endyear":year} and gets project_name from session
    args = {}
    project_file = helpers.safe_join(loaddir(model), project_name+'.prj')
    args['D'] = loaddata(project_file)
    startyear = data.get("startyear")
    if startyear:
        args["startyear"] = int(startyear)
    endyear = data.get("endyear")
    if endyear:
        args["endyear"] = int(endyear)
    try:
        data_file_path = runsimulation(**args) 
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify({"status":"OK", "reason":'performed simulation for the project %s' % project_name})
#    options = {
#        'cache_timeout': model.get_send_file_max_age(example_excel_file_name),
#        'conditional': True,
#        'attachment_filename': downloadName
#    }
#    return helpers.send_file(data_file_path, **options)
