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
from server.webapp.utils import (load_model, save_model, save_working_model_as_default,
                                 revert_working_model_to_default, pick_params, check_project_name, for_fe)
from server.webapp.utils import report_exception, check_project_exists
from flask.ext.login import login_required, current_user  # pylint: disable=E0611,F0401
from flask import current_app
from signal import *
from server.webapp.dbconn import db
# TODO fix after v2
# from sim.autofit import autofit
# TODO fix after v2
# from sim.updatedata import updatedata

# route prefix: /api/model
model = Blueprint('model',  __name__, static_folder='../static')
model.config = {}


###### old webapp/parameters.py

'''
Reads in parameter table from optima and provides additional functions
'''
from optima.parameters import loadpartable
parameter_list = loadpartable()

def input_parameter(short):
    entry = [param for param in parameter_list if short in param['short']]
    if entry:
        return entry[0]
    else:
        return None

def input_parameters(short):
    return [param for param in parameter_list if short in param['short']]

def input_parameter_name(short):
    param = input_parameter(short)
    if param:
        return param['name']
    else:
        return None

# TODO: is this still necessary??
def parameter_name(key):
    if not type(key)==list: key=[key]
    entry = [param for param in parameter_list if ''.join(param['short'])==''.join(key)]
    if entry:
        return entry[0]['name']
    else:
        return None

#######

def add_calibration_parameters(project_instance, result=None):
    """
    picks the parameters for calibration based on D as dictionary and the parameters settings
    """
    # BUG: parameters.parameters doesn't exist
    from parameters import parameters
    if not project_instance.parsets:
        raise Exception("No parsets are present for the project %s" % project_instance.uid)

#    from optima.nested import getnested
    calibrate_parameters = [p for p in parameters() if 'calibration' in p and p['calibration']]
    if result is None:
        result = {}
    result['F'] = []  # TBC by Cliff: which part of pars is it? project_instance.parsets['default'].pars
#    M = D_dict.get('M', {})
    M_out = []  # TBC by Cliff: is it still needed or gone?
#    if M:
#        for parameter in calibrate_parameters:
#            keys = parameter['keys']
#            entry = {}
#            entry['name'] = keys
#            entry['title'] = parameter['name']
#            entry['data'] = getnested(M, keys, safe = True) TODO restore
#            M_out.append(entry)
    result['M'] = M_out
    return result


@model.record
def record_params(setup_state):
    app = setup_state.app
    model.config = dict([(key, value) for (key, value) in app.config.iteritems()])


@model.route('/calibrate/auto', methods=['POST'])
@login_required
@check_project_name
@check_project_exists
@report_exception
def doAutoCalibration():
    """
    Uses provided parameters to auto calibrate the model (update it with these data)

    TODO: do it with the project which is currently in scope

    """
    current_app.logger.debug('auto calibration data: %s' % request.data)
    data = json.loads(request.data)

    project_name = request.project_name
    project_id = request.project_id
    # TODO fix after v2 - we might want to switch to Celery instead
    # can_start, can_join, current_calculation = start_or_report_calculation(
    #     current_user.id, project_id, autofit, db.session)
    can_start, can_join, current_calculation = (False, False, None)
    if can_start:
        args = {'verbose': 1}
        startyear = data.get("startyear")
        if startyear:
            args["startyear"] = int(startyear)
        endyear = data.get("endyear")
        if endyear:
            args["endyear"] = int(endyear)
        timelimit = int(data.get("timelimit"))  # for the thread
        args["timelimit"] = timelimit  # for the autocalibrate function
        # TODO fix after v2
        # CalculatingThread(db.engine, current_user, project_id, timelimit, 1, autofit, args).start() #run it once
        msg = "Starting thread for user %s project %s:%s" % (current_user.name, project_id, project_name)
        return jsonify({"result": msg, "join": True})
    else:
        msg = "Thread for user %s project %s:%s (%s) has already started" % (
            current_user.name, project_id, project_name, current_calculation)
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
    return jsonify({"result": "autofit calculation for user %s project %s:%s requested to stop" %
                  (current_user.name, project_id, project_name)})


@model.route('/working')
@login_required
@check_project_name
@report_exception
def getWorkingModel():
    """ Returns the working model of project. """
    # TODO: this would not make sense anymore, because we'd only need results for a specific parset.
    project_instance = {}
    # TODO fix after v2
    # Make sure model is calibrating
    error_text = None
    status = 'Done'
    response_status = 200
    # project_id = request.project_id
    # if check_calculation(current_user.id, project_id, autofit, db.session):
    #     status = 'Running'
    # else:
    #     current_app.logger.debug('No longer calibrating')
    #     status, error_text, _ = check_calculation_status(current_user.id, project_id, autofit, db.session)
    #     if status in good_exit_status:
    #         status = 'Done'
    #     else:
    #         status = 'Failed'
    # if status!='Failed':
    #     D_dict = load_model(project_id, working_model = True, from_json = False)

    # result = {'graph': D_dict.get('plot',{}).get('E',{})}
    # result['status'] = status
    # if error_text:
    #     result['exception'] = error_text

    # if status == 'Failed':
    #     response_status = 500
    result = add_calibration_parameters(project_instance, result)
    return jsonify(result), response_status


@model.route('/calibrate/save', methods=['POST'])
@login_required
@check_project_name
@check_project_exists
@report_exception
def saveCalibrationModel():
    """ Saves working model as the default model """
    # TODO: we no longer need to save the whole project, only the results for the specific parset.
    # get project name
    result = {'graph': {}}
    # project_id = request.project_id
    # D_dict = save_working_model_as_default(project_id)
    # result = {'graph': D_dict.get('plot',{}).get('E',{})}
    # result = add_calibration_parameters(D_dict, result)
    return jsonify(result)


@model.route('/calibrate/revert', methods=['POST'])
@login_required
@check_project_name
@check_project_exists
@report_exception
def revertCalibrationModel():
    """ Revert working model to the default model """
    # TODO: we would only need to delete temporary result corresponding to the given project / parset.
    # get project name
    result = {'graph': {}}
    # project_id = request.project_id
    # D_dict = revert_working_model_to_default(project_id)
    # result = {'graph': D_dict.get('plot',{}).get('E',{})}
    # result = add_calibration_parameters(D_dict, result)
    return jsonify(result)


@model.route('/calibrate/manual', methods=['POST'])
@login_required
@check_project_name
@check_project_exists
@report_exception
def doManualCalibration():
    # TODO: we can do that once we know which data we are going to save and where they would go
    # most probably this will be done as a Parset update.
    """
    Uses provided parameters to manually calibrate the model (update it with these data)

    TODO: do it with the project which is currently in scope

    """
    result = {'graph': {}}
    # data = json.loads(request.data)
    # current_app.logger.debug("/api/model/calibrate/manual %s" % data)
    # # get project name
    # project_id = request.project_id

    # #expects json: {"startyear":year,"endyear":year} and gets project_name from session
    # args = {}
    # startyear = data.get("startyear")
    # if startyear:
    #     args["startyear"] = int(startyear)
    # endyear = data.get("endyear")
    # if endyear:
    #     args["endyear"] = int(endyear)
    # dosave = data.get("dosave")
    # D = load_model(project_id)
    # args['D'] = D
    # F = fromjson(data.get("F",{}))
    # args['F'] = F
    # Mlist = data.get("M",[])
    # args['Mlist'] = Mlist
    # # TODO fix after v2
    # # D = manualfit(**args)
    # D_dict = tojson(D)
    # if dosave:
    #     current_app.logger.debug("model: %s" % project_id)
    #     save_model(project_id, D_dict)
    # result = {'graph': D_dict.get('plot',{}).get('E',{})}
    result = add_calibration_parameters(D_dict, result)
    return jsonify(result)


@model.route('/calibrate/parameters')
@login_required
@check_project_name
def getModelCalibrateParameters():
    """ Returns the parameters of the given model. """
    # TODO: find out how do we show calibration parameters now.
    project_instance = load_model(request.project_id, from_json=False)
    result = add_calibration_parameters(project_instance)
    return jsonify(result)


@model.route('/data')
@login_required
@check_project_name
def getModel():
    # TODO: make it a Data resource
    """ Returns the model (aka D or data) for the currently open project. """
    project_instance = load_model(request.project_id, from_json=False)
    project_data = project_instance.data
    # TODO: see abouve
    return jsonify({'data': {}})


@model.route('/data/<key>')
@login_required
@check_project_name
def getModelGroup(key):
    # TODO: make it a DataKey resource
    """ Returns the subset with the given key for the D (model) in the open project."""
    current_app.logger.debug("getModelGroup: %s" % key)
    project_instance = load_model(request.project_id, from_json=False)
    the_group = {}  # project_instance.data.get(key, {})
    return jsonify({'data': the_group})


@model.route('/data/<key>/<subkey>')
@login_required
@check_project_name
def getModelSubGroup(key, subkey):
    # TODO (if necessary): either make it a DataSubKey resource,
    # or generalise and make it possible to retrieve data by json path
    # (but the simpler the better, so probably just the option 1)
    """ Returns the subset with the given key and subkey for the D (model) in the open project. """
    current_app.logger.debug("getModelSubGroup: %s %s" % (key, subkey))
    project_instance = load_model(request.project_id, from_json=False)
    print "data", project_instance.data.keys()
#    the_group = project_instance.data.get(key, {})
    the_subgroup = {}  # the_group.get(subkey, {})
    return jsonify({'data': the_subgroup})


@model.route('/data/<key>', methods=['POST'])
@login_required
@check_project_name
@report_exception
def setModelGroup(key):
    # TODO: this should be part of DataKey CRUD
    """ Stores the provided data as a subset with the given key for the D (model) in the open project. """
    # data = json.loads(request.data)
    # current_app.logger.debug("set parameters key: %s for data: %s" % (key, data))
    # project_id = request.project_id
    # D_dict = load_model(project_id, from_json=False)
    # D_dict[key] = data
    # save_model(project_id, D_dict)
    # return jsonify({"project": project_id, "key": key})
    return jsonify({"key": key})


@model.route('/view', methods=['POST'])
@login_required
@check_project_name
@report_exception
def doRunSimulation():
    # TODO: this should have the "parset id" and "project id" parameters.
    # the flow:
    # retrieve parset with the given id / project id, hydrate the project
    # call p.runsim for the given parset
    # what to do with the results? We might want to store them temporarily somewhere
    # (we only save them if the user confirms)
    # make a graph based on results and return it
    # TBC with Cliff / Robyn: will there still be "startyear" and "endyear" parameters?
    """
    Starts simulation for the given project and given date range.

    Returns back the file with the simulation data.

    """
    # data = json.loads(request.data)

    # args = {}
    # D_dict = load_model(request.project_id, from_json = False)
    # result = {'graph': D_dict.get('plot',{}).get('E',{})}
    # if not result:
    #     D = fromjson(D_dict)
    #     args['D'] = D
    #     startyear = data.get("startyear")
    #     if startyear:
    #         args["startyear"] = int(startyear)
    #     endyear = data.get("endyear")
    #     if endyear:
    #         args["endyear"] = int(endyear)
    #     args["dosave"] = False
    #     # TODO fix after v2
    #     # D = runsimulation(**args)
    #     D_dict = tojson(D)
    #     save_model(request.project_id, D_dict)
    #     result = {'graph':D_dict.get('plot',{}).get('E',{})}
    result = {'graph': {}}
    result = add_calibration_parameters(D_dict, result)
    return jsonify(result)


@model.route('/costcoverage', methods=['POST'])
@login_required
@check_project_name
def doCostCoverage():  # pylint: disable=R0914
    # What it should now do (I think):
    # either get a progset id or assume that it is given the progset with parameters
    # (in Optima 1.0 we sent parameters which may or may not be saved for the given program)
    # generate (or retrieve? ) cost-coverage for that progset id
    # cost-coverage is 3 dictionaries with the graphs already formatted in mpld3
    # if do_save is true, save the corresponding progset (Actually the progset parameters)
    """ Calls makecco with parameters supplied from frontend """
    dict_fig_cc = dict()
    dict_fig_co = dict()
    dict_fig_cco = dict()
    effectnames = dict()

    # def findIndex(sequence, function):
    #     """ Returns the first index in the sequence where function(item) == True. """
    #     for index, item in enumerate(sequence):
    #         if function(item):
    #             return index

    # data = json.loads(request.data)
    # current_app.logger.debug("/costcoverage" % data)
    # args = {}
    # D = load_model(request.project_id)
    # args = pick_params(["progname", "ccparams"], data, args)
    # do_save = data.get('doSave')
    # try:
    #     if 'ccparams' in args:
    #         args['ccparams'] = {key: float(value) for key, value in args['ccparams'].items() if value}

    #     programIndex = findIndex(D['programs'], lambda item: item['name'] == args['progname'])

    #     effects = data.get('all_effects')
    #     new_coparams = data.get('all_coparams')
    #     if effects and len(effects):
    #         new_effects = []
    #         for i in xrange(len(effects)):
    #             effect = effects[str(i)]
    #             if new_coparams[i] and len(new_coparams[i]) == 4 and \
    #                     all(coparam is not None for coparam in new_coparams[i]):
    #                 if len(effect) < 3:
    #                     effect.append(new_coparams[i][:])
    #                 else:
    #                     effect[2] = new_coparams[i][:]
    #             new_effects.append(effect)
    #         D['programs'][programIndex]['effects'] = new_effects
    #     args['D'] = D
    #     # effectnames are actually effects
    #     # TODO fix after v2
    #     # plotdata_cco, plotdata_co, plotdata_cc, effectnames, D = plotallcurves(**args)
    #     # dict_fig_cc = generate_cost_coverage_chart(plotdata_cc)
    #     # dict_fig_co = map(lambda key: generate_coverage_outcome_chart(plotdata_co[key]), plotdata_co.keys())
    #     # dict_fig_cco = map(lambda key: generate_cost_outcome_chart(plotdata_cco[key]), plotdata_cco.keys())
    #     if do_save:
    #         D_dict = tojson(D)
    #         save_model(request.project_id, D_dict)
    # except Exception:
    #     var = traceback.format_exc()
    #     return jsonify({"exception": var}), 500
    return jsonify({
        "effectnames": for_fe(effectnames),
        "fig_cc": dict_fig_cc,
        "fig_co": dict_fig_co,
        "fig_cco": dict_fig_cco})


@model.route('/costcoverage/effect', methods=['POST'])
@login_required
@check_project_name
def doCostCoverageEffect():
    # TODO what should happen here:
    # only a particular effect parameters are edited
    # TBC by Robyn how it would look now (which part of progset it is)
    data = json.loads(request.data)
    current_app.logger.debug("/costcoverage/effect(%s)" % data)
    args = {}
    args = pick_params(["progname", "effect", "ccparams", "coparams"], data, args)
    effect = args['effect']
    dict_fig_co = dict()
    dict_fig_cco = dict()
    # args['D'] = load_model(request.project_id)
    # try:
    #     if not args.get('effect'):
    #         return jsonify({'reason': 'No effect has been specified'}), 500
    #     if args.get('ccparams'):
    #         args['ccparams'] = dict([(
    #             key, (float(param) if param else None)) for (key, param) in args['ccparams'].iteritems()])
    #     if args.get('coparams'):
    #         args['coparams'] = map(
    #             lambda param: float(param) if param or (type(param) is int and param == 0) else None,
    #             args['coparams'])
    #     # effectnames are actually effects
    #     # TODO fix after v2
    #     # plotdata, plotdata_co, _ = makecco(**args) # plotdata is actually plotdata_cco
    #     # dict_fig_co = generate_coverage_outcome_chart(plotdata_co)
    #     # dict_fig_cco = generate_cost_outcome_chart(plotdata)
    #     dict_fig_co = dict()
    #     dict_fig_cco = dict()
    # except Exception:
    #     var = traceback.format_exc()
    #     return jsonify({"exception": var}), 500
    return jsonify({
        "effect": args['effect'],
        "fig_co": dict_fig_co,
        "fig_cco": dict_fig_cco})


@model.route('/reloadSpreadsheet/<project_id>', methods=['GET'])
@login_required
@check_project_name
@report_exception
def reloadSpreadsheet(project_id):
    """
    Reload the excel spreadsheet and re-run the simulations.
    """
    # TODO what should happen here:
    # (probably this could be part of project resource?)
    # call runsim again for the default parset and save the results
    # TODO verify with Cliff / Robyn if it would make sense for Optima 2.0
    # from server.webapp.utils import load_project

    # project = load_project(project_id)
    # D = load_model(project_id)
    # # TODO fix after v2
    # # D = updatedata(D, input_programs = project.programs, savetofile = False, rerun = True)
    # D_dict = tojson(D)
    # save_model(project_id, D_dict)
    return jsonify({})
