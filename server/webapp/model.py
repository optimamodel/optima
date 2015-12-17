from flask import Blueprint, request, jsonify
import json
import traceback
from server.webapp.async_calculate import CalculatingThread, start_or_report_calculation
from server.webapp.async_calculate import cancel_calculation, check_calculation
from server.webapp.async_calculate import check_calculation_status, good_exit_status
# TODO fix after v2
# from sim.manualfit import manualfit
from dataio import fromjson, tojson
# TODO fix after v2
# from sim.runsimulation import runsimulation
# TODO fix after v2
# from sim.makeccocs import makecco, plotallcurves #, default_effectname, default_ccparams, default_coparams
from server.webapp.utils import load_model, save_model, save_working_model_as_default, revert_working_model_to_default, pick_params, check_project_name, for_fe
from server.webapp.utils import report_exception, check_project_exists
from flask.ext.login import login_required, current_user # pylint: disable=E0611,F0401
from flask import current_app
from signal import *
from server.webapp.dbconn import db
# TODO fix after v2
# from sim.autofit import autofit
# TODO fix after v2
# from sim.updatedata import updatedata
from server.webapp.plotting import generate_cost_coverage_chart, generate_coverage_outcome_chart, generate_cost_outcome_chart

# route prefix: /api/model
model = Blueprint('model',  __name__, static_folder = '../static')
model.config = {}

def add_calibration_parameters(project_instance, result = None):
    """
    picks the parameters for calibration based on D as dictionary and the parameters settings
    """
    from parameters import parameters
    if not project_instance.parsets:
        raise Exception("No parsets are present for the project %s" % project_instance.id)

#    from optima.nested import getnested
    calibrate_parameters = [p for p in parameters() if 'calibration' in p and p['calibration']]
    if result is None: result = {}
    print "default parset", project_instance.parsets['default'].pars
    result['F'] = [] # project_instance.parsets['default'].pars 
    # !!!!! TODO make project_instance.parsets['default'].pars (which is odict) serializable
#    M = D_dict.get('M', {})
    M_out = []
#    if M:
#        for parameter in calibrate_parameters:
#            keys = parameter['keys']
#            entry = {}
#            entry['name'] = keys
#            entry['title'] = parameter['name']
#            entry['data'] = getnested(M, keys, safe = True) TODO restore
#            M_out.append(entry)
    result['M']=M_out
    return result



@model.record
def record_params(setup_state):
    app = setup_state.app
    model.config = dict([(key,value) for (key,value) in app.config.iteritems()])


@model.route('/calibrate/auto', methods=['POST'])
@login_required
@check_project_name
@check_project_exists
@report_exception()
def doAutoCalibration():
    """
    Uses provided parameters to auto calibrate the model (update it with these data)

    TODO: do it with the project which is currently in scope

    """
    current_app.logger.debug('auto calibration data: %s' % request.data)
    data = json.loads(request.data)

    project_name = request.project_name
    project_id = request.project_id
    # TODO fix after v2
    # can_start, can_join, current_calculation = start_or_report_calculation(
    #     current_user.id, project_id, autofit, db.session)
    can_start, can_join, current_calculation = (False, False, None)
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
        # TODO fix after v2
        # CalculatingThread(db.engine, current_user, project_id, timelimit, 1, autofit, args).start() #run it once
        msg = "Starting thread for user %s project %s:%s" % (current_user.name, project_id, project_name)
        return jsonify({"result": msg, "join": True})
    else:
        msg = "Thread for user %s project %s:%s (%s) has already started" % (current_user.name, project_id, project_name, current_calculation)
        return jsonify({"result": msg, "join": can_join})

@model.route('/calibrate/stop')
@login_required
@check_project_name
def stopCalibration():
    """ Stops calibration """
    project_id = request.project_id
    project_name = request.project_name
    # TODO fix after v2
    # cancel_calculation(current_user.id, project_id, autofit, db.session)
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
    error_text = None
    # TODO fix after v2
    # if check_calculation(current_user.id, project_id, autofit, db.session):
    if False:
        status = 'Running'
    else:
        current_app.logger.debug('No longer calibrating')
        status, error_text, _ = check_calculation_status(current_user.id, project_id, autofit, db.session)
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
@check_project_exists
@report_exception()
def saveCalibrationModel():
    """ Saves working model as the default model """
    # get project name
    project_id = request.project_id
    D_dict = save_working_model_as_default(project_id)
    result = {'graph': D_dict.get('plot',{}).get('E',{})}
    result = add_calibration_parameters(D_dict, result)
    return jsonify(result)


@model.route('/calibrate/revert', methods=['POST'])
@login_required
@check_project_name
@check_project_exists
@report_exception()
def revertCalibrationModel():
    """ Revert working model to the default model """
    # get project name
    project_id = request.project_id
    D_dict = revert_working_model_to_default(project_id)
    result = {'graph': D_dict.get('plot',{}).get('E',{})}
    result = add_calibration_parameters(D_dict, result)
    return jsonify(result)

@model.route('/calibrate/manual', methods=['POST'])
@login_required
@check_project_name
@check_project_exists
@report_exception()
def doManualCalibration():
    """
    Uses provided parameters to manually calibrate the model (update it with these data)

    TODO: do it with the project which is currently in scope

    """
    data = json.loads(request.data)
    current_app.logger.debug("/api/model/calibrate/manual %s" % data)
    # get project name
    project_id = request.project_id

    #expects json: {"startyear":year,"endyear":year} and gets project_name from session
    args = {}
    startyear = data.get("startyear")
    if startyear:
        args["startyear"] = int(startyear)
    endyear = data.get("endyear")
    if endyear:
        args["endyear"] = int(endyear)
    dosave = data.get("dosave")
    D = load_model(project_id)
    args['D'] = D
    F = fromjson(data.get("F",{}))
    args['F'] = F
    Mlist = data.get("M",[])
    args['Mlist'] = Mlist
    # TODO fix after v2
    # D = manualfit(**args)
    D_dict = tojson(D)
    if dosave:
        current_app.logger.debug("model: %s" % project_id)
        save_model(project_id, D_dict)
    result = {'graph': D_dict.get('plot',{}).get('E',{})}
    result = add_calibration_parameters(D_dict, result)
    return jsonify(result)

@model.route('/calibrate/parameters')
@login_required
@check_project_name
def getModelCalibrateParameters():
    """ Returns the parameters of the given model. """
    project_instance = load_model(request.project_id, from_json = False)
    result = add_calibration_parameters(project_instance)
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
    project_instance = load_model(request.project_id, from_json = False)
    print "data", project_instance.data.keys()
    the_group = project_instance.data.get(key,{})
    the_subgroup = the_group.get(subkey, {})
    return jsonify({'data': the_subgroup})

@model.route('/data/<key>', methods=['POST'])
@login_required
@check_project_name
@report_exception()
def setModelGroup(key):
    """ Stores the provided data as a subset with the given key for the D (model) in the open project. """
    data = json.loads(request.data)
    current_app.logger.debug("set parameters key: %s for data: %s" % (key, data))
    project_id = request.project_id
    D_dict = load_model(project_id, from_json = False)
    D_dict[key] = data
    save_model(project_id, D_dict)
    return jsonify({"project":project_id, "key":key})

@model.route('/view', methods=['POST'])
@login_required
@check_project_name
@report_exception()
def doRunSimulation():
    """
    Starts simulation for the given project and given date range.

    Returns back the file with the simulation data.

    """
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
        # TODO fix after v2
        # D = runsimulation(**args)
        D_dict = tojson(D)
        save_model(request.project_id, D_dict)
        result = {'graph':D_dict.get('plot',{}).get('E',{})}
    result = add_calibration_parameters(D_dict, result)
    return jsonify(result)

@model.route('/costcoverage', methods=['POST'])
@login_required
@check_project_name
def doCostCoverage(): # pylint: disable=R0914
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

        programIndex = findIndex(D['programs'], lambda item: item['name'] == args['progname'])

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
        # effectnames are actually effects
        # TODO fix after v2
        # plotdata_cco, plotdata_co, plotdata_cc, effectnames, D = plotallcurves(**args)
        # dict_fig_cc = generate_cost_coverage_chart(plotdata_cc)
        # dict_fig_co = map(lambda key: generate_coverage_outcome_chart(plotdata_co[key]), plotdata_co.keys())
        # dict_fig_cco = map(lambda key: generate_cost_outcome_chart(plotdata_cco[key]), plotdata_cco.keys())
        dict_fig_cc = dict()
        dict_fig_co = dict()
        dict_fig_cco = dict()
        if do_save:
            D_dict = tojson(D)
            save_model(request.project_id, D_dict)
    except Exception:
        var = traceback.format_exc()
        return jsonify({"exception":var}), 500
    return jsonify({
        "effectnames": for_fe(effectnames),
        "fig_cc": dict_fig_cc,
        "fig_co": dict_fig_co,
        "fig_cco": dict_fig_cco})

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
        if args.get('coparams'):
            args['coparams'] = map(lambda param: float(param) if param or (type(param) is int and param == 0) else None, args['coparams'])
        # effectnames are actually effects
        # TODO fix after v2
        # plotdata, plotdata_co, _ = makecco(**args) # plotdata is actually plotdata_cco
        # dict_fig_co = generate_coverage_outcome_chart(plotdata_co)
        # dict_fig_cco = generate_cost_outcome_chart(plotdata)
        dict_fig_co = dict()
        dict_fig_cco = dict()
    except Exception:
        var = traceback.format_exc()
        return jsonify({"exception":var}), 500
    return jsonify({
        "effect": args['effect'],
        "fig_co": dict_fig_co,
        "fig_cco": dict_fig_cco })


@model.route('/reloadSpreadsheet/<project_id>', methods=['GET'])
@login_required
@check_project_name
@report_exception()
def reloadSpreadsheet(project_id):
    """
    Reload the excel spreadsheet and re-run the simulations.
    """
    from server.webapp.utils import load_project

    project = load_project(project_id)
    D = load_model(project_id)
    # TODO fix after v2
    # D = updatedata(D, input_programs = project.programs, savetofile = False, rerun = True)
    D_dict = tojson(D)
    save_model(project_id, D_dict)
    return jsonify({})
