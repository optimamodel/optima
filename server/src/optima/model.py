from flask import Blueprint, request, jsonify
import json
import traceback
from async_calculate import CalculatingThread, start_or_report_calculation, cancel_calculation, check_calculation
from sim.manualfit import manualfit
from sim.bunch import bunchify
from sim.runsimulation import runsimulation
from sim.makeccocs import makecco, plotallcurves, default_effectname, default_ccparams, default_coparams
from utils import load_model, save_model, save_working_model_as_default, revert_working_model_to_default, project_exists, pick_params, check_project_name, for_fe
from utils import report_exception
from flask.ext.login import login_required, current_user
from flask import current_app
from signal import *
from dbconn import db
from sim.autofit import autofit

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
    reply = {'status':'NOK'}
    current_app.logger.debug('data: %s' % request.data)
    data = json.loads(request.data)

    project_name = request.project_name
    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % prj_name
        return jsonify(reply)
    try:
        can_start, can_join, current_calculation = start_or_report_calculation(current_user.id, project_name, autofit, db.engine)
        if can_start:
            args = {'verbose':0}
            startyear = data.get("startyear")
            if startyear:
                args["startyear"] = int(startyear)
            endyear = data.get("endyear")
            if endyear:
                args["endyear"] = int(endyear)
            timelimit = int(data.get("timelimit")) # for the thread
            args["timelimit"] = 10 # for the autocalibrate function

            CalculatingThread(db.engine, current_user, project_name, timelimit, autofit, args).start()
            msg = "Starting thread for user %s project %s" % (current_user.name, project_name)
            return json.dumps({"status":"OK", "result": msg, "join":True})
        else:
            msg = "Thread for user %s project %s (%s) has already started" % (current_user.name, project_name, current_calculation)
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
    cancel_calculation(current_user.id, prj_name, autofit, db.engine)
    return json.dumps({"status":"OK", "result": "autofit calculation for user %s project %s requested to stop" % (current_user.name, prj_name)})

"""
Returns the working model of project.
"""
@model.route('/working')
@login_required
@check_project_name
@report_exception()
def getWorkingModel():
    D_dict = {}
    # Make sure model is calibrating
    prj_name = request.project_name
    if check_calculation(current_user.id, prj_name, autofit, db.engine):
        D_dict = load_model(prj_name, working_model = True, as_bunch = False)
        status = 'Running'
    else:
        status = 'Done'
    result = {'graph': D_dict.get('plot',{}).get('E',{})}
    result['status'] = status
    return jsonify(result)

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
    current_app.logger.debug("/api/model/calibrate/manual %s" % data)
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
            current_app.logger.debug("model: %s" % project_name)
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
    current_app.logger.debug("getModelParameters: %s" % group)
    D_dict = load_model(request.project_name, as_bunch = False)
    the_group = D_dict.get(group, {})
    current_app.logger.debug("the_group: %s" % the_group)
    return json.dumps(the_group)


"""
Returns the parameters of the given model in the given group / subgroup/ project.
"""
@model.route('/parameters/<group>/<subgroup>')
@login_required
@check_project_name
def getModelSubParameters(group, subgroup):
    current_app.logger.debug("getModelSubParameters: %s %s" % (group, subgroup))
    D_dict = load_model(request.project_name, as_bunch = False)
    the_group = D_dict.get(group,{})
    the_subgroup = the_group.get(subgroup, {})
    current_app.logger.debug("result: %s" % the_subgroup)
    return jsonify(the_subgroup)


"""
Sets the given group parameters for the given model.
"""
@model.route('/parameters/<group>', methods=['POST'])
@login_required
@check_project_name
def setModelParameters(group):
    data = json.loads(request.data)
    current_app.logger.debug("set parameters group: %s for data: %s" % (group, data))
    project_name = request.project_name
    try:
        D_dict = load_model(project_name, as_bunch = False)
        D_dict[group] = data
        save_model(project_name, D_dict)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
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
        current_app.logger.debug("D-dict F: %s" % D_dict['F'])
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
    D = load_model(request.project_name)
    args = pick_params(["progname", "ccparams", "coparams"], data, args)
    do_save = data.get('doSave')
    try:
        if not args.get('ccparams'):
            args['ccparams'] = default_ccparams
        if not args.get('coparams'):
            args['coparams'] = default_coparams
        args['ccparams'] = [float(param) for param in args['ccparams']]
        args['coparams'] = [float(param) for param in args['coparams']]
        args['coparams'] = default_coparams # otherwise the effect changes will be overwritten

        args['makeplot'] = 0 # don't do plotting in SIM
        if do_save:
            progname = args['progname']
            effects = data.get('all_effects')
            new_coparams = data.get('all_coparams')
            new_effects = []
            for i in xrange(len(effects)):
                effect = effects[str(i)]
                effect[2] = [[new_coparams[i][0], new_coparams[i][1]], [new_coparams[i][2], new_coparams[i][3]]]
                new_effects.append(effect)
            D.programs[progname] = new_effects
        args['D'] = D
        plotdata, plotdata_co, plotdata_cc, effectnames, D = plotallcurves(**args)
        if do_save:
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
    current_app.logger.debug("/costcoverage/effect(%s)" % data)
    args = {}
    args = pick_params(["progname", "effectname", "ccparams", "coparams"], data, args)
    args['D'] = load_model(request.project_name)
    try:
        if not args.get('ccparams'):
            args['ccparams'] = default_ccparams
        if not args.get('coparams'):
            args['coparams'] = default_coparams
        if not args.get('effectname'):
            args['effectname'] = default_effectname
        args['ccparams'] = [float(param) for param in args['ccparams']]
        args['coparams'] = [float(param) for param in args['coparams']]
        args['makeplot'] = 0 # don't do plotting in SIM
        plotdata, plotdata_co, storeparams = makecco(**args)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify({"status":"OK", "plotdata": for_fe(plotdata), \
        "plotdata_co": for_fe(plotdata_co), "effectname": args['effectname']})