#!/bin/env python
# -*- coding: utf-8 -*-
"""
Optimization Module
~~~~~~~~~~~~~~~~~~~

1. Start an optimization request
2. Stop an optimization
3. Save current optimization model
4. Revert to the last saved model
"""
import json
import traceback
from flask import request, jsonify, Blueprint, current_app
from flask.ext.login import login_required, current_user # pylint: disable=E0611,F0401
from server.webapp.dbconn import db
from server.webapp.async_calculate import CalculatingThread, start_or_report_calculation
from server.webapp.async_calculate import cancel_calculation, check_calculation
from server.webapp.async_calculate import check_calculation_status, good_exit_status
from server.webapp.utils import check_project_name, check_project_exists, load_model, save_model
from server.webapp.utils import revert_working_model_to_default, save_working_model_as_default, report_exception
# TODO fix after v2
# from sim.optimize import optimize, saveoptimization, defaultoptimizations, defaultobjectives, defaultconstraints
from dataio import fromjson, tojson

# route prefix: /api/analysis/optimization
optimization = Blueprint('optimization',  __name__, static_folder = '../static')

@optimization.route('/list')
@login_required
@check_project_name
@check_project_exists
@report_exception
def getOptimizationParameters():
    """ retrieve list of optimizations defined by the user, with parameters """
    current_app.logger.debug("/api/analysis/optimization/list")
    # get project name
    project_name = request.project_name
    project_id = request.project_id
    D_dict = load_model(project_id, from_json = False)
    if not 'optimizations' in D_dict:
        # save the defaults once and forever, so that we won't painfully retrieve it later
        D = fromjson(D_dict)
        if 'data' in D:
            # TODO fix after v2
            # optimizations = tojson(defaultoptimizations(D))
            # D_dict['optimizations'] = optimizations
            save_model(project_id, D_dict)
        else:
            optimizations = []
    else:
        optimizations = D_dict['optimizations']
    return jsonify({'optimizations':optimizations})


@optimization.route('/start', methods=['POST'])
@login_required
@check_project_name
@check_project_exists
@report_exception
def startOptimization():
    """ Start optimization """
    data = json.loads(request.data)
    current_app.logger.debug("optimize: %s" % data)
    # get project name
    project_id = request.project_id
    project_name = request.project_name

    # TODO fix after v2
    # can_start, can_join, current_calculation = start_or_report_calculation(
    #     current_user.id, project_id, optimize, db.session)
    can_start, can_join, current_calculation = (False, False, None)

    if can_start:
        # Prepare arguments
        args = {'verbose':2}
        objectives = data.get('objectives')
        if objectives:
            args['objectives'] = fromjson( objectives )
        constraints = data.get('constraints')
        if constraints:
            args['constraints'] = fromjson( constraints )
        name = data.get('name')
        if name:
            args['name'] = name
        timelimit = int(data.get("timelimit")) # for the thread
#            args["maxiters"] = 5 #test
        numiter = 1 #IMPORTANT: only run it once
        # TODO fix after v2
        # CalculatingThread(db.engine, current_user, project_id, timelimit, numiter, optimize, args, with_stoppingfunc = True).start()
        msg = "Starting optimization thread for user %s project %s:%s" % (current_user.name, project_id, project_name)
        current_app.logger.debug(msg)
        return jsonify({"result": msg, "join":True})
    else:
        msg = "Thread for user %s project %s:%s (%s) has already started" % (current_user.name, project_id, project_name, current_calculation)
        return jsonify({"result": msg, "join":can_join})

@optimization.route('/stop')
@login_required
@check_project_name
def stopCalibration():
    """ Stops calibration """
    project_id = request.project_id
    project_name = request.project_name
    # TODO fix after v2
    # cancel_calculation(current_user.id, project_id, optimize, db.session)
    return jsonify({"result": "optimize calculation for user %s project %s:%s requested to stop" \
        % (current_user.name, project_id, project_name)})

@optimization.route('/working')
@login_required
@check_project_name
@report_exception
def getWorkingModel(): # pylint: disable=R0912, R0914, R0915
    """ Returns the working model for optimization. """
    import datetime
    import dateutil.tz
    from copy import deepcopy

    current_app.logger.debug("/api/optimization/working")
    result = {}
    D_dict = {}
    # Get optimization working data
    project_id = request.project_id
    D_dict_new = load_model(project_id, working_model = False, from_json = False)
    new_optimizations = D_dict_new.get('optimizations')
    if not new_optimizations:
        D_new = fromjson(D_dict_new)
        # TODO fix after v2
        # new_optimizations = tojson(defaultoptimizations(D_new))
        new_optimizations = {}
    error_text = None
    status = None

    if check_calculation(current_user.id, project_id, optimize, db.session):
        status = 'Running'
    else:
        current_app.logger.debug("optimization for project %s was stopped or cancelled" % project_id)
        async_status, error_text, stop_time = check_calculation_status(current_user.id, project_id, optimize, db.session)
        now_time = datetime.datetime.now(dateutil.tz.tzutc()) #time in DB is UTC-aware
        if async_status == 'unknown':
            status = 'Done'
        elif async_status in good_exit_status:
            if stop_time and stop_time<now_time: #actually stopped
                status = 'Done'
                current_app.logger.debug("optimization thread for project %s actually stopped" % project_id)
            else: #not yet stopped
                status = 'Stopping'
                current_app.logger.debug("optimization thread for project %s is about to stop" % project_id)
        else:
            status = 'Failed'

    if status!='Failed': D_dict = load_model(project_id, working_model = True, from_json = False)

    optimizations = D_dict.get('optimizations')
    names = [item['name'] for item in optimizations] if optimizations else ['Default']
    current_app.logger.debug("optimization names: %s" % names)
    is_dirty = False
    for new_index, new_optimization in enumerate(new_optimizations):
        #trying to update the results in the current model with the available results from the working model
        name = new_optimization['name']
        if optimizations and name in names:
            index = names.index(name)
            if ('result' in optimizations[index]) and (new_optimization.get('result')!=optimizations[index]['result']):
                current_app.logger.debug("Found updated result for: name %s" % name)
                new_optimizations[new_index] = deepcopy(optimizations[index])
                #warn that these results are transient
                is_dirty = True

    response_status = 200
    result['status'] = status
    result['optimizations'] = new_optimizations
    result['dirty'] = is_dirty
    if error_text:
        result['exception'] = error_text
    return jsonify(result), response_status


@optimization.route('/save', methods=['POST'])
@login_required
@check_project_name
@check_project_exists
@report_exception
def saveModel():
    """ Saves working model as the default model """
    # get project name
    project_id = request.project_id
    project_name = request.project_name
    # now, save the working model, read results and save for the optimization with the given name
    D_dict = save_working_model_as_default(project_id)
    return jsonify({'optimizations': D_dict['optimizations']})

@optimization.route('/revert', methods=['POST'])
@login_required
@check_project_name
@check_project_exists
@report_exception
def revertWorkingModel():
    """ Revert working model to the default model """
    # get project name
    project_id = request.project_id
    D_dict = revert_working_model_to_default(project_id)
    reply = {'optimizations': D_dict.get('optimizations')}
    if not reply['optimizations']:
        D = fromjson(D_dict)
        # TODO fix after v2
        # reply['optimizations'] = tojson(defaultoptimizations(D))
    return jsonify(reply)


@optimization.route('/remove/<name>', methods=['POST'])
@login_required
@check_project_name
@check_project_exists
@report_exception
def removeOptimizationSet(name):
    """ Removes given optimization from the optimization set """
    from sim.optimize import removeoptimization
    # get project name
    project_id = request.project_id
    D_dict = load_model(project_id, from_json = False)
    #no need to convert for that, so don't bother
    D_dict = removeoptimization(D_dict, name)
    save_model(project_id, D_dict)
    reply = {'name': 'deleted', 'optimizations': D_dict['optimizations']}
    return jsonify(reply)

@optimization.route('/create', methods=['POST'])
@login_required
@check_project_name
@check_project_exists
@report_exception
def create_optimization():
    """ Creates a new optimization from the optimization set """
    data = json.loads(request.data)

    name = data.get('name')
    if not name:
        reply = {'reason': 'Please provide a name for new optimization'}
        return jsonify(reply), 500

    # get project id and name
    project_id = request.project_id
    D_dict = load_model(project_id, from_json = False)
    objectives = data.get('objectives')
    constraints = data.get('constraints')
    if not objectives or not constraints:
        D = fromjson(D_dict)
        if objectives:
            objectives = fromjson( objectives )
        else:
            # TODO fix after v2
            # objectives = defaultobjectives(D)
            pass
        if constraints:
            constraints = fromjson( constraints )
        else:
            # TODO fix after v2
            # constraints = defaultconstraints(D)
            pass

    #save new optimization slot - no need to convert back and forth the whole project for that now
    # TODO fix after v2
    # D_dict = saveoptimization(D_dict, name, objectives, constraints)
    D_dict['optimizations'] = tojson(D_dict['optimizations'])
    save_model(project_id, D_dict)
    #return all available optimizations back
    reply = {'optimizations': D_dict['optimizations']}
    return jsonify(reply)
