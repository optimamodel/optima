import os
import shutil
from flask import Flask, Blueprint, helpers, request, jsonify, session, redirect
from werkzeug import secure_filename
from generators.line import generatedata
import json
import traceback
import sys
from sim.dataio import loaddata, savedata, DATADIR, PROJECTDIR
from sim.updatedata import updatedata
from sim.loadspreadsheet import loadspreadsheet
from sim.makeproject import makeproject
from sim.manualfit import manualfit
from sim.autofit import autofit
from sim.bunch import unbunchify, bunchify, Bunch as struct
from sim.runsimulation import runsimulation
from sim.optimize import optimize
from sim.epiresults import epiresults
from sim.makeccocs import makecco
from utils import loaddir, load_model, save_model, project_exists, pick_params
from flask.ext.login import login_required

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
@login_required
def doAutoCalibration():
    reply = {'status':'NOK'}
    print('data: %s' % request.data)
    data = json.loads(request.data)

    # get project name 
    try:
        project_name = request.headers['project_name']
    except:
        project_name = ''

    if project_name == '':
        reply['reason'] = 'No project is open'
        return jsonify(reply)

    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % project_name
        return jsonify(reply)

    file_name = helpers.safe_join(PROJECTDIR, project_name+'.prj')
    print("project file_name: %s" % file_name)
    fits = autofit(file_name, data)
    # autofit is not implemented yet, so just run the simulation #TODO #FIXME
    try:
        D = load_model(project_name)
        D = runsimulation(**args) 
        D = epiresults(D)
        D_dict = unbunchify(D)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify(D_dict.get('O',{}))


#    print("fits: %s" % fits)
#    fits = [unbunchify(x) for x in fits]
#    print("unbunchified fits: %s" % fits)
#    return jsonify(fits[0])


""" 
Uses provided parameters to manually calibrate the model (update it with these data) 
TODO: do it with the project which is currently in scope
"""
@model.route('/calibrate/manual', methods=['POST'])
@login_required
def doManualCalibration():
    data = json.loads(request.data)
   
    # get project name
    try:
        project_name = request.headers['project_name']
    except:
        project_name = ''

    if project_name == '':
        return jsonify({'status':'NOK', 'reason':'no project is open'})
    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % project_name
    file_name = helpers.safe_join(PROJECTDIR, project_name+'.prj')
    print("project file_name: %s" % file_name)

    #expects json: {"startyear":year,"endyear":year} and gets project_name from session
    args = {}
    startyear = data.get("startyear")
    if startyear:
        args["startyear"] = int(startyear)
    endyear = data.get("endyear")
    if endyear:
        args["endyear"] = int(endyear)
    dosave = data.get("dosave")
    if dosave:
        args["dosave"] = dosave
    try:
        D = load_model(project_name)
        args['D'] = D
        F = bunchify(data.get("F",{}))
        args['F'] = F
        D = manualfit(**args) 
        D_dict = unbunchify(D)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify(D_dict.get('O',{}))


"""
Returns the parameters of the given model.
"""
@model.route('/parameters')
@login_required
def getModel():
    
    try:
        project_name = request.headers['project_name']
    except:
        project_name = ''

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
@login_required
def getModelParameters(group):
    print("getModelParameters: %s" % group)
   
    try:
        project_name = request.headers['project_name']
    except:
        project_name = ''

    if project_name == '':
        return jsonify({'status':'NOK', 'reason':'no project is open'})
    D = load_model(project_name)
    result = unbunchify(D)
    print "result: %s" % result
    return jsonify(result.get(group,{}))


"""
Returns the parameters of the given model in the given group / subgroup/ project.
"""
@model.route('/parameters/<group>/<subgroup>')
@login_required
def getModelSubParameters(group, subgroup):
    print("getModelSubParameters: %s %s" % (group, subgroup))
    
    try:
        project_name = request.headers['project_name']
    except:
        project_name = ''

    if project_name == '':
        return jsonify({'status':'NOK', 'reason':'no project is open'})
    D = load_model(project_name)
    result = unbunchify(D)
    the_group = result.get(group,{})
    the_subgroup = the_group.get(subgroup, {})
    print "result: %s" % the_subgroup
    return jsonify(the_subgroup)


"""
Sets the given group parameters for the given model.
"""
@model.route('/parameters/<group>', methods=['POST'])
@login_required
def setModelParameters(group):
    data = json.loads(request.data)
    print("set parameters group: %s for data: %s" % (group, data))
    
    # get project name
    try:
        project_name = request.headers['project_name']
    except:
        project_name = ''
   
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
@login_required
def doRunSimulation():
    data = json.loads(request.data)
    
    # get project name
    try:
        project_name = request.headers['project_name']
    except:
        project_name = ''
    
    if project_name == '':
        return jsonify({"status":"NOK", "reason":"no project is open"})

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


"""
Calls makecco with parameters supplied from frontend
"""
@model.route('/costcoverage', methods=['POST'])
@login_required
def doCostCoverage():
    data = json.loads(request.data)
    
    # get project name
    try:
        project_name = request.headers['project_name']
    except:
        project_name = ''

    if project_name == '':
        return jsonify({"status":"NOK", "reason":"no project is open"})
    args = {}
    args['D'] = load_model(project_name)
    args = pick_params(["progname", "ccparams", "coparams"], data, args)
    try:
        plotdata, plotdata_cc, plotdata_co = makecco(**args)
#        D = runsimulation(**args) 
#        D = epiresults(D)
#        D_dict = unbunchify(D)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify({"status":"OK", "plotdata": plotdata, "plotdata_cc": plotdata_cc, "plotdata_co": plotdata_co})
#    return jsonify(D_dict.get('O',{}))
