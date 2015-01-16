from flask import Blueprint, request, jsonify
import json
import traceback
from async_calculate import CalculatingThread, start_or_report_calculation, cancel_calculation
from async_calculate import check_calculation, check_calculation_status, good_exit_status
from sim.manualfit import manualfit
from sim.bunch import bunchify
from sim.runsimulation import runsimulation
from sim.makeccocs import makecco, plotallcurves #, default_effectname, default_ccparams, default_coparams
from utils import load_model, save_model, save_working_model_as_default, revert_working_model_to_default, project_exists, pick_params, check_project_name, for_fe
from utils import report_exception
from flask.ext.login import login_required, current_user
from flask import current_app
from signal import *
from dbconn import db
from sim.autofit import autofit

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
    result['G'] = D_dict.get('G', {})
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
    reply = {'status':'NOK'}
    current_app.logger.debug('data: %s' % request.data)
    data = json.loads(request.data)

    project_name = request.project_name
    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % prj_name
        return jsonify(reply)
    try:
        can_start, can_join, current_calculation = start_or_report_calculation(current_user.id, project_name, autofit, db.session)
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

@model.route('/calibrate/stop')
@login_required
@check_project_name
def stopCalibration():
    """ Stops calibration """
    prj_name = request.project_name
    cancel_calculation(current_user.id, prj_name, autofit, db.session)
    return json.dumps({"status":"OK", "result": "autofit calculation for user %s project %s requested to stop" % (current_user.name, prj_name)})

@model.route('/working')
@login_required
@check_project_name
@report_exception()
def getWorkingModel():
    """ Returns the working model of project. """
    D_dict = {}
    # Make sure model is calibrating
    prj_name = request.project_name
    error_text = None
    if check_calculation(current_user.id, prj_name, autofit, db.session):
        D_dict = load_model(prj_name, working_model = True, as_bunch = False)
        status = 'Running'
    else:
        current_app.logger.debug('No longer calibrating')
        status, error_text = check_calculation_status(current_user.id, prj_name, autofit, db.session)
        if status in good_exit_status:
            status = 'Done'
        else:
            status = 'NOK'
    result = {'graph': D_dict.get('plot',{}).get('E',{})}
    result['status'] = status
    if error_text:
        result['exception'] = error_text
    result = add_calibration_parameters(D_dict, result)
    return jsonify(result)

@model.route('/calibrate/save', methods=['POST'])
@login_required
@check_project_name
def saveCalibrationModel():
    """ Saves working model as the default model """
    reply = {'status':'NOK'}

    # get project name
    project_name = request.project_name
    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % project_name
        return jsonify(reply)

    try:
        D_dict = save_working_model_as_default(project_name)
        result = {'graph': D_dict.get('plot',{}).get('E',{})}
        result = add_calibration_parameters(D_dict, result)
        return jsonify(result)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})


@model.route('/calibrate/revert', methods=['POST'])
@login_required
@check_project_name
def revertCalibrationModel():
    """ Revert working model to the default model """
    reply = {'status':'NOK'}

    # get project name
    project_name = request.project_name
    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % project_name
        return jsonify(reply)
    try:
        D_dict = revert_working_model_to_default(project_name)
        result = {'graph': D_dict.get('plot',{}).get('E',{})}
        result = add_calibration_parameters(D_dict, result)
        return jsonify(result)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})

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
        Mlist = data.get("M",[])
        args['Mlist'] = Mlist
        D = manualfit(**args)
        D_dict = D.toDict()
        if dosave:
            current_app.logger.debug("model: %s" % project_name)
            save_model(project_name, D_dict)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
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
    D = load_model(request.project_name, as_bunch = True)
    D_dict = D.toDict()
    result = add_calibration_parameters(D_dict)
    return jsonify(result)

@model.route('/parameters')
@login_required
@check_project_name
def getModel():
    """ Returns the parameters of the given model. """
    D = load_model(request.project_name, as_bunch = False)
    return jsonify(result)

@model.route('/parameters/<group>')
@login_required
@check_project_name
def getModelParameters(group):
    """ Returns the parameters of the given model in the given group."""
    current_app.logger.debug("getModelParameters: %s" % group)
    D_dict = load_model(request.project_name, as_bunch = False)
    the_group = D_dict.get(group, {})
    return json.dumps(the_group)

@model.route('/parameters/<group>/<subgroup>')
@login_required
@check_project_name
def getModelSubParameters(group, subgroup):
    """ Returns the parameters of the given model in the given group / subgroup/ project. """
    current_app.logger.debug("getModelSubParameters: %s %s" % (group, subgroup))
    D_dict = load_model(request.project_name, as_bunch = False)
    the_group = D_dict.get(group,{})
    the_subgroup = the_group.get(subgroup, {})
    return jsonify(the_subgroup)

@model.route('/parameters/<group>', methods=['POST'])
@login_required
@check_project_name
def setModelParameters(group):
    """ Sets the given group parameters for the given model. """
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

@model.route('/view', methods=['POST'])
@login_required
@check_project_name
def doRunSimulation():
    """
    Starts simulation for the given project and given date range.

    Returns back the file with the simulation data.
    (?) #FIXME find out how to use it

    """
    data = json.loads(request.data)

    #expects json: {"startyear":year,"endyear":year} and gets project_name from session
    args = {}
    D = load_model(request.project_name)
    D_dict = D.toDict()
    result = {'graph': D_dict.get('plot',{}).get('E',{})}
    result = add_calibration_parameters(D_dict, result)
    if not result:
        try:
            args['D'] = D
            startyear = data.get("startyear")
            if startyear:
                args["startyear"] = int(startyear)
            endyear = data.get("endyear")
            if endyear:
                args["endyear"] = int(endyear)
            args["makeplot"] = 0
            args["dosave"] = False
            D = runsimulation(**args)
            D_dict = D.toDict()
            save_model(request.project_name, D_dict)
            result = {'graph':D_dict.get('plot',{}).get('E',{})}
            result = add_calibration_parameters(D_dict, result)
            return jsonify(result)
        except Exception, err:
            var = traceback.format_exc()
            return jsonify({"status":"NOK", "exception":var})
    return jsonify(result)

@model.route('/costcoverage', methods=['POST'])
@login_required
@check_project_name
def doCostCoverage():
    """ Calls makecco with parameters supplied from frontend """
    data = json.loads(request.data)
    current_app.logger.debug("/costcoverage" % data)
    args = {}
    D = load_model(request.project_name)
    args = pick_params(["progname", "ccparams", "coparams", "ccplot"], data, args)
    do_save = data.get('doSave')
    try:
        if args.get('ccparams'):args['ccparams'] = [float(param) if param else None for param in args['ccparams']]
        if args.get('coparams'):del args['coparams'] 

        args['makeplot'] = 0 # don't do plotting in SIM
        progname = args['progname']
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
            D.programs[progname]['effects'] = new_effects
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
    args = pick_params(["progname", "effect", "ccparams", "coparams", "ccplot"], data, args)
    args['D'] = load_model(request.project_name)
    try:
        if not args.get('effect'):
            return jsonify({'status':'NOK','reason':'No effect has been specified'})
        if args.get('ccparams'):args['ccparams'] = [float(param) if param else None for param in args['ccparams']]
        if args.get('coparams'):args['coparams'] = [float(param) for param in args['coparams']]
        args['makeplot'] = 0 # don't do plotting in SIM
        plotdata, plotdata_co, storeparams_co = makecco(**args)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify({"status":"OK", "plotdata": for_fe(plotdata), \
        "plotdata_co": for_fe(plotdata_co), "effect": args['effect']})
