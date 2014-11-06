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
from sim.bunch import unbunchify, Bunch as struct
from sim.runsimulation import runsimulation
from sim.optimize import optimize
from sim.epiresults import epiresults
from utils import loaddir, load_model, save_model, project_exists

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

    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % project_name
        return jsonify(reply)

    file_name = helpers.safe_join(PROJECTDIR, project_name+'.prj')
    print("project file_name: %s" % file_name)
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

    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % project_name

    file_name = helpers.safe_join(PROJECTDIR, project_name+'.prj')
    print("project file_name: %s" % file_name)
    D = manualfit(file_name, data)
    print("D: %s" % D)
    fits = {} #todo: how to get graphs from the model after calibration? @cliffkerr ?
    return jsonify(fits[0])


"""
Returns the parameters of the given model.
"""
@model.route('/parameters')
def getModel():
    project_name = session.get('project_name', '')
    if project_name == '':
        return jsonify({'status':'NOK', 'reason':'no project is open'})
    D = load_model(project_name)
    result = unbunchify(D)
    print "result: %s" % result
    return jsonify(result)


"""
Returns the parameters of the given model in the given group.
"""
@model.route('/parameters/<group>')
def getModelParameters(group):
    project_name = session.get('project_name', '')
    if project_name == '':
        return jsonify({'status':'NOK', 'reason':'no project is open'})
    D = load_model(project_name)
    result = unbunchify(D)
    print "result: %s" % result
    return jsonify(result.get(group,{}))

"""
Sets the given group parameters for the given model.
"""
@model.route('/parameters/<group>', methods=['POST'])
def setModelParameters(group):
    data = json.loads(request.data)
    print("set parameters group: %s for data: %s" % (group, data))
    project_name = session.get('project_name', '')
    if project_name == '':
        return jsonify({'status':'NOK', 'reason':'no project is open'})
    try:
        D = load_model(project_name)
        D_dict = unbunchify(D)
        D_dict[group] = data
        D_mod = struct(D_dict)
        save_model(loaddir(model), project_name, D_mod)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})        
    print "D as dict: %s" % D_dict
    return jsonify({"status":"OK", "project":project_name, "group":group})


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
    args['D'] = load_model(project_name)
    startyear = data.get("startyear")
    if startyear:
        args["startyear"] = int(startyear)
    endyear = data.get("endyear")
    if endyear:
        args["endyear"] = int(endyear)
    try:
        D = runsimulation(**args) 
        D = epiresults(D)
        D_dict = unbunchify(D)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify(D_dict.get('O',{}))
#    options = {
#        'cache_timeout': model.get_send_file_max_age(example_excel_file_name),
#        'conditional': True,
#        'attachment_filename': downloadName
#    }
#    return helpers.send_file(data_file_path, **options)
