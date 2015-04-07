from flask import Blueprint, request, jsonify
import json
import traceback
from async_calculate import CalculatingThread, start_or_report_calculation, cancel_calculation
from async_calculate import check_calculation, check_calculation_status, good_exit_status
from sim.manualfit import manualfit
from sim.dataio import fromjson, tojson
from sim.runsimulation import runsimulation
from sim.makeccocs import makecco, plotallcurves #, default_effectname, default_ccparams, default_coparams
from utils import load_model, save_model, save_working_model_as_default, revert_working_model_to_default, project_exists, pick_params, check_project_name, for_fe
from utils import report_exception
from flask.ext.login import login_required, current_user
from flask import current_app
from signal import *
from dbconn import db
from sim.autofit import autofit
from sim.updatedata import updatedata

# route prefix: /api/model
model = Blueprint('model',  __name__, static_folder = '../static')
model.config = {}

def add_calibration_parameters(D_dict, result = None):
    """
    picks the parameters for calibration based on D as dictionary and the parameters settings
    """
    from sim.parameters import parameters
    from sim.nested import getnested
    calibrate_parameters = [p for p in parameters() if 'calibration' in p and p['calibration']]
    if result is None: result = {}
    result['F'] = D_dict.get('F', {})
    M = D_dict.get('M', {})
    M_out = []
    if M:
        for parameter in calibrate_parameters:
            keys = parameter['keys']
            entry = {}
            entry['name'] = keys
            entry['title'] = parameter['name']
            entry['data'] = getnested(M, keys, safe = True)
            M_out.append(entry)
    result['M']=M_out
    return result



@model.record
def record_params(setup_state):
    app = setup_state.app
    model.config = dict([(key,value) for (key,value) in app.config.iteritems()])


@model.route('/calibrate/auto', methods=['POST'])
@login_required
@check_project_name
def doAutoCalibration():
    """
    Uses provided parameters to auto calibrate the model (update it with these data)

    TODO: do it with the project which is currently in scope

    """
    current_app.logger.debug('auto calibration data: %s' % request.data)
    data = json.loads(request.data)

    project_name = request.project_name
    project_id = request.project_id
    if not project_exists(project_id):
        reply = {'reason': 'File for project %s does not exist' % project_id}
        return jsonify(reply), 500
    try:
        can_start, can_join, current_calculation = start_or_report_calculation(current_user.id, project_id, autofit, db.session)
        if can_start:
            args = {'verbose':1}
            startyear = data.get("startyear")
            if startyear:
                args["startyear"] = int(startyear)
            endyear = data.get("endyear")
            if endyear:
                args["endyear"] = int(endyear)
            timelimit = int(data.get("timelimit")) # for the thread
            args["timelimit"] = timelimit # for the autocalibrate function
            CalculatingThread(db.engine, current_user, project_id, timelimit, 1, autofit, args).start() #run it once
            msg = "Starting thread for user %s project %s:%s" % (current_user.name, project_id, project_name)
            return jsonify({"result": msg, "join": True})
        else:
            msg = "Thread for user %s project %s:%s (%s) has already started" % (current_user.name, project_id, project_name, current_calculation)
            return jsonify({"result": msg, "join": can_join})
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"exception":var}), 500

@model.route('/calibrate/stop')
@login_required
@check_project_name
def stopCalibration():
    """ Stops calibration """
    project_id = request.project_id
    project_name = request.project_name
    cancel_calculation(current_user.id, project_id, autofit, db.session)
    return jsonify({"result": "autofit calculation for user %s project %s:%s requested to stop" % \
        (current_user.name, project_id, project_name)})

@model.route('/working')
@login_required
@check_project_name
@report_exception()
def getWorkingModel():
    """ Returns the working model of project. """
    D_dict = {}
    # Make sure model is calibrating
    project_id = request.project_id
    project_name = request.project_name
    error_text = None
    stop_time = None
    if check_calculation(current_user.id, project_id, autofit, db.session):
        status = 'Running'
    else:
        current_app.logger.debug('No longer calibrating')
        status, error_text, stop_time = check_calculation_status(current_user.id, project_id, autofit, db.session)
        if status in good_exit_status:
            status = 'Done'
        else:
            status = 'Failed'
    if status!='Failed': D_dict = load_model(project_id, working_model = True, from_json = False)

    result = {'graph': D_dict.get('plot',{}).get('E',{})}
    result['status'] = status
    if error_text:
        result['exception'] = error_text

    response_status = 200
    if status == 'Failed':
        response_status = 500
    result = add_calibration_parameters(D_dict, result)
    return jsonify(result), response_status

@model.route('/calibrate/save', methods=['POST'])
@login_required
@check_project_name
def saveCalibrationModel():
    """ Saves working model as the default model """
    # get project name
    project_name = request.project_name
    project_id = request.project_id
    if not project_exists(project_id):
        reply = {'reason': 'File for project %s does not exist' % project_id}
        return jsonify(reply), 500

    try:
        D_dict = save_working_model_as_default(project_id)
        result = {'graph': D_dict.get('plot',{}).get('E',{})}
        result = add_calibration_parameters(D_dict, result)
        return jsonify(result)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"exception":var}), 500


@model.route('/calibrate/revert', methods=['POST'])
@login_required
@check_project_name
def revertCalibrationModel():
    """ Revert working model to the default model """
    # get project name
    project_name = request.project_name
    project_id = request.project_id
    if not project_exists(project_id):
        reply = {'reason': 'File for project %s does not exist' % project_id}
        return jsonify(reply), 500
    try:
        D_dict = revert_working_model_to_default(project_id)
        result = {'graph': D_dict.get('plot',{}).get('E',{})}
        result = add_calibration_parameters(D_dict, result)
        return jsonify(result)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"exception":var}), 500

@model.route('/calibrate/manual', methods=['POST'])
@login_required
@check_project_name
def doManualCalibration():
    """
    Uses provided parameters to manually calibrate the model (update it with these data)

    TODO: do it with the project which is currently in scope

    """
    data = json.loads(request.data)
    current_app.logger.debug("/api/model/calibrate/manual %s" % data)
    # get project name
    project_name = request.project_name
    project_id = request.project_id
    if not project_exists(project_id):
        reply = {'reason': 'Project %s does not exist' % project_id}
        return jsonify(reply), 500

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
        D = load_model(project_id)
        args['D'] = D
        F = fromjson(data.get("F",{}))
        args['F'] = F
        Mlist = data.get("M",[])
        args['Mlist'] = Mlist
        D = manualfit(**args)
        D_dict = tojson(D)
        if dosave:
            current_app.logger.debug("model: %s" % project_id)
            save_model(project_id, D_dict)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"exception":var}), 500
    result = {'graph': D_dict.get('plot',{}).get('E',{})}
    result = add_calibration_parameters(D_dict, result)
    return jsonify(result)

@model.route('/calibrate/parameters')
@login_required
@check_project_name
def getModelCalibrateParameters():
    """ Returns the parameters of the given model. """
    from sim.parameters import parameters
    from sim.manualfit import updateP
    from sim.nested import getnested
    calibrate_parameters = [p for p in parameters() if 'calibration' in p and p['calibration']]
    D_dict = load_model(request.project_id, from_json = False)
    result = add_calibration_parameters(D_dict)
    return jsonify(result)

@model.route('/data')
@login_required
@check_project_name
def getModel():
    """ Returns the model (aka D or data) for the currently open project. """
    D_dict = load_model(request.project_id, from_json = False)
    return jsonify(D_dict)

@model.route('/data/<key>')
@login_required
@check_project_name
def getModelGroup(key):
    """ Returns the subset with the given key for the D (model) in the open project."""
    current_app.logger.debug("getModelGroup: %s" % key)
    D_dict = load_model(request.project_id, from_json = False)
    the_group = D_dict.get(key, {})
    return jsonify({'data': the_group})

@model.route('/data/<key>/<subkey>')
@login_required
@check_project_name
def getModelSubGroup(key, subkey):
    """ Returns the subset with the given key and subkey for the D (model) in the open project. """
    current_app.logger.debug("getModelSubGroup: %s %s" % (key, subkey))
    D_dict = load_model(request.project_id, from_json = False)
    the_group = D_dict.get(key,{})
    the_subgroup = the_group.get(subkey, {})
    return jsonify({'data': the_subgroup})

@model.route('/data/<key>', methods=['POST'])
@login_required
@check_project_name
def setModelGroup(key):
    """ Stores the provided data as a subset with the given key for the D (model) in the open project. """
    data = json.loads(request.data)
    current_app.logger.debug("set parameters group: %s for data: %s" % (group, data))
    project_name = request.project_name
    project_id = request.project_id
    try:
        D_dict = load_model(project_id, from_json = False)
        D_dict[group] = data
        save_model(project_id, D_dict)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"exception":var}), 500
    return jsonify({"project":project_id, "group":group})

@model.route('/view', methods=['POST'])
@login_required
@check_project_name
@report_exception()
def doRunSimulation():
    """
    Starts simulation for the given project and given date range.

    Returns back the file with the simulation data.
    (?) #FIXME find out how to use it

    """
    import os
    data = json.loads(request.data)

    args = {}
    D_dict = load_model(request.project_id, from_json = False)
    result = {'graph': D_dict.get('plot',{}).get('E',{})}
    if not result:
        D = fromjson(D_dict)
        args['D'] = D
        startyear = data.get("startyear")
        if startyear:
            args["startyear"] = int(startyear)
        endyear = data.get("endyear")
        if endyear:
            args["endyear"] = int(endyear)
        args["dosave"] = False
        D = runsimulation(**args)
        D_dict = tojson(D)
        save_model(request.project_id, D_dict)
        result = {'graph':D_dict.get('plot',{}).get('E',{})}
    result = add_calibration_parameters(D_dict, result)
    return jsonify(result)

@model.route('/costcoverage', methods=['POST'])
@login_required
@check_project_name
def doCostCoverage():
    """ Calls makecco with parameters supplied from frontend """

    def findIndex(sequence, function):
      """ Returns the first index in the sequence where function(item) == True. """
      for index, item in enumerate(sequence):
        if function(item):
          return index

    data = json.loads(request.data)
    current_app.logger.debug("/costcoverage" % data)
    args = {}
    D = load_model(request.project_id)
    args = pick_params(["progname", "ccparams"], data, args)
    do_save = data.get('doSave')
    try:
        if 'ccparams' in args:
            args['ccparams'] = {key: float(value) for key, value in args['ccparams'].items() if value}

        programIndex = findIndex(D['programs'], lambda item: item['name'] == args['progname']);

        effects = data.get('all_effects')
        new_coparams = data.get('all_coparams')
        if effects and len(effects):
            new_effects = []
            for i in xrange(len(effects)):
                effect = effects[str(i)]
                if new_coparams[i] and len(new_coparams[i])==4 and all(coparam is not None for coparam in new_coparams[i]):
                    if len(effect)<3:
                        effect.append(new_coparams[i][:])
                    else:
                        effect[2] = new_coparams[i][:]
                new_effects.append(effect)
            D['programs'][programIndex]['effects'] = new_effects
        args['D'] = D

        plotdata, plotdata_co, plotdata_cc, effectnames, D = plotallcurves(**args) #effectnames are actually effects
        if do_save:
            D_dict = tojson(D)
            save_model(request.project_id, D_dict)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"exception":var}), 500
    return jsonify({"plotdata": for_fe(plotdata), \
        "plotdata_co": for_fe(plotdata_co), "plotdata_cc": for_fe(plotdata_cc), "effectnames": for_fe(effectnames)})

@model.route('/costcoverage/effect', methods=['POST'])
@login_required
@check_project_name
def doCostCoverageEffect():
    data = json.loads(request.data)
    current_app.logger.debug("/costcoverage/effect(%s)" % data)
    args = {}
    args = pick_params(["progname", "effect", "ccparams", "coparams"], data, args)
    args['D'] = load_model(request.project_id)
    try:
        if not args.get('effect'):
            return jsonify({'reason':'No effect has been specified'}), 500
        if args.get('ccparams'):
            args['ccparams'] = dict([(key, (float(param) if param else None)) for (key,param) in args['ccparams'].iteritems()])
        if args.get('coparams'):args['coparams'] = [float(param) for param in args['coparams']]
        plotdata, plotdata_co, storeparams_co = makecco(**args)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"exception":var}), 500
    return jsonify({"plotdata": for_fe(plotdata), \
        "plotdata_co": for_fe(plotdata_co), "effect": args['effect']})


@model.route('/reloadSpreadsheet/<project_id>', methods=['GET'])
@login_required
@check_project_name
@report_exception()
def reloadSpreadsheet(project_id):
    """
    Reload the excel spreadsheet and re-run the simulations.
    """
    from utils import load_project

    project = load_project(project_id)
    D = load_model(project_id)
    D = updatedata(D, input_programs = project.programs, savetofile = False, rerun = True)

    return jsonify({})
