from flask import Blueprint, request, jsonify
import json
import traceback
from async_calculate import CalculatingThread, sentinel
from sim.manualfit import manualfit
from sim.bunch import bunchify
from sim.runsimulation import runsimulation
from sim.makeccocs import makecco, plotallcurves, default_effectname
from utils import load_model, save_model, save_working_model_as_default, revert_working_model_to_default, project_exists, pick_params, check_project_name, for_fe
from flask.ext.login import login_required, current_user
from signal import *
import sys
from dbconn import db

""" route prefix: /api/model """
model = Blueprint('model',  __name__, static_folder = '../static')
model.config = {}


@model.record
def record_params(setup_state):
    app = setup_state.app
    model.config = dict([(key,value) for (key,value) in app.config.iteritems()])

"""
Uses provided parameters to auto calibrate the model (update it with these data)
TODO: do it with the project which is currently in scope
"""
@model.route('/calibrate/auto', methods=['POST'])
@login_required
@check_project_name
def doAutoCalibration():
    from sim.autofit import autofit
    reply = {'status':'NOK'}
    print('data: %s' % request.data)
    data = json.loads(request.data)

    project_name = request.project_name
    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % prj_name
        return jsonify(reply)
    try:
        if not project_name in sentinel['projects'] or not sentinel['projects'][project_name]:
            args = {}
            startyear = data.get("startyear")
            if startyear:
                args["startyear"] = int(startyear)
            endyear = data.get("endyear")
            if endyear:
                args["endyear"] = int(endyear)
            timelimit = int(data.get("timelimit")) # for the thread
            args["timelimit"] = 10 # for the autocalibrate function

            CalculatingThread(db.engine, sentinel, current_user, project_name, timelimit, autofit, args).start()
            msg = "Starting thread for user %s project %s" % (current_user.name, project_name)
            return json.dumps({"status":"OK", "result": msg, "join":True})
        else:
            current_calculation = sentinel['projects'][project_name]
            print('sentinel object: %s' % sentinel)
            msg = "Thread for user %s project %s (%s) has already started" % (current_user.name, project_name, current_calculation)
            can_join = current_calculation==autofit.__name__
            return json.dumps({"status":"OK", "result": msg, "join":can_join})
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})

"""
Stops calibration
"""
@model.route('/calibrate/stop')
@login_required
@check_project_name
def stopCalibration():
    prj_name = request.project_name
    if prj_name in sentinel['projects']:
        sentinel['projects'][prj_name] = False
    return json.dumps({"status":"OK", "result": "thread for user %s project %s stopped" % (current_user.name, prj_name)})

"""
Returns the working model of project.
"""
@model.route('/working')
@login_required
@check_project_name
def getWorkingModel():
    from sim.autofit import autofit

    # Make sure model is calibrating
    try:
        prj_name = request.project_name
        D_dict = load_model(prj_name, working_model = True, as_bunch = False)
        result = {'graph': D_dict.get('plot',{}).get('E',{})}
        if prj_name in sentinel['projects'] and sentinel['projects'][prj_name]==autofit.__name__:
            result['status'] = 'Running'
        else:
            print("no longer calibrating")
            result['status'] = 'Done'
        return jsonify(result)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})

"""
Saves working model as the default model
"""
@model.route('/calibrate/save', methods=['POST'])
@login_required
@check_project_name
def saveCalibrationModel():
    reply = {'status':'NOK'}

    # get project name
    project_name = request.project_name
    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % project_name
        return jsonify(reply)

    try:
        D_dict = save_working_model_as_default(project_name)
        return jsonify(D_dict.get('plot',{}).get('E',{}))
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})


"""
Revert working model to the default model
"""
@model.route('/calibrate/revert', methods=['POST'])
@login_required
@check_project_name
def revertCalibrationModel():
    reply = {'status':'NOK'}

    # get project name
    project_name = request.project_name
    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % project_name
        return jsonify(reply)
    try:
        D_dict = revert_working_model_to_default(project_name)
        return jsonify(D_dict.get('plot',{}).get('E',{}))
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})

"""
Uses provided parameters to manually calibrate the model (update it with these data)
TODO: do it with the project which is currently in scope
"""
@model.route('/calibrate/manual', methods=['POST'])
@login_required
@check_project_name
def doManualCalibration():
    data = json.loads(request.data)
    print("/api/model/calibrate/manual %s" % data)
    # get project name
    project_name = request.project_name
    if not project_exists(project_name):
        reply['reason'] = 'Project %s does not exist' % project_name

    #expects json: {"startyear":year,"endyear":year} and gets project_name from session
    args = {}
    startyear = data.get("startyear")
    if startyear:
        args["startyear"] = int(startyear)
    endyear = data.get("endyear")
    if endyear:
        args["endyear"] = int(endyear)
    dosave = data.get("dosave")
    try:
        D = load_model(project_name)
        args['D'] = D
        F = bunchify(data.get("F",{}))
        args['F'] = F
        D = manualfit(**args)
        D_dict = D.toDict()
        if dosave:
            print("model: %s" % project_name)
            save_model(project_name, D_dict)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify(D_dict.get('plot',{}).get('E',{}))

"""
Returns the parameters of the given model.
"""
@model.route('/parameters')
@login_required
@check_project_name
def getModel():
    D = load_model(request.project_name)
    result = D.toDict()
    return jsonify(result)

"""
Returns the parameters of the given model in the given group.
"""
@model.route('/parameters/<group>')
@login_required
@check_project_name
def getModelParameters(group):
    print("getModelParameters: %s" % group)
    D_dict = load_model(request.project_name, as_bunch = False)
    the_group = D_dict.get(group, {})
    print("the_group: %s" % the_group)
    return json.dumps(the_group)


"""
Returns the parameters of the given model in the given group / subgroup/ project.
"""
@model.route('/parameters/<group>/<subgroup>')
@login_required
@check_project_name
def getModelSubParameters(group, subgroup):
    print("getModelSubParameters: %s %s" % (group, subgroup))
    D_dict = load_model(request.project_name, as_bunch = False)
    the_group = D_dict.get(group,{})
    the_subgroup = the_group.get(subgroup, {})
    print "result: %s" % the_subgroup
    return jsonify(the_subgroup)


"""
Sets the given group parameters for the given model.
"""
@model.route('/parameters/<group>', methods=['POST'])
@login_required
@check_project_name
def setModelParameters(group):
    data = json.loads(request.data)
    print("set parameters group: %s for data: %s" % (group, data))
    project_name = request.project_name
    try:
        D_dict = load_model(project_name, as_bunch = False)
        D_dict[group] = data
        save_model(project_name, D_dict)
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
@check_project_name
def doRunSimulation():
    data = json.loads(request.data)

    #expects json: {"startyear":year,"endyear":year} and gets project_name from session
    args = {}
    args['D'] = load_model(request.project_name)
    startyear = data.get("startyear")
    if startyear:
        args["startyear"] = int(startyear)
    endyear = data.get("endyear")
    if endyear:
        args["endyear"] = int(endyear)
    try:
        D = runsimulation(**args)
        D_dict = D.toDict()
        print ("D-dict F: %s" % D_dict['F'])
        save_model(request.project_name, D_dict)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify(D_dict.get('plot',{}).get('E',{}))


"""
Calls makecco with parameters supplied from frontend
"""
@model.route('/costcoverage', methods=['POST'])
@login_required
@check_project_name
def doCostCoverage():
    data = json.loads(request.data)
    args = {}
    args['D'] = load_model(request.project_name)
    args = pick_params(["progname", "ccparams", "coparams"], data, args)
    try:
        if not args.get('ccparams'):
            args['ccparams'] = [0.9, 0.2, 800000.0, 7e6]
        if not args.get('coparams'):
            args['coparams'] = []
        args['ccparams'] = [float(param) for param in args['ccparams']]
        args['coparams'] = [float(param) for param in args['coparams']]
        plotdata, plotdata_co, plotdata_cc, effectnames, D = plotallcurves(**args)
        if args.get('dosave'):
            D_dict = D.toDict()
            save_model(request.project_name, D_dict)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify({"status":"OK", "plotdata": for_fe(plotdata), \
        "plotdata_co": for_fe(plotdata_co), "plotdata_cc": for_fe(plotdata_cc), "effectnames": for_fe(effectnames)})

@model.route('/costcoverage/effect', methods=['POST'])
@login_required
@check_project_name
def doCostCoverageEffect():
    data = json.loads(request.data)
    print("/costcoverage/effect(%s)" % data)
    args = {}
    args = pick_params(["progname", "effectname", "ccparams", "coparams"], data, args)
    args['D'] = load_model(request.project_name)
    try:
        if not args.get('ccparams'):
            args['ccparams'] = [0.9, 0.2, 800000.0, 7e6]
        if not args.get('coparams'):
            args['coparams'] = []
        if not args.get('effectname'):
            args['effectname'] = default_effectname
        args['coparams'] = [float(param) for param in args['coparams']]
        plotdata, plotdata_co, storeparams = makecco(**args)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify({"status":"OK", "plotdata": for_fe(plotdata), \
        "plotdata_co": for_fe(plotdata_co), "effectname": args['effectname']})
