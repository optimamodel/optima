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
from flask.ext.login import login_required, current_user
from dbconn import db
from async_calculate import CalculatingThread, start_or_report_calculation, cancel_calculation, check_calculation
from async_calculate import check_calculation_status, good_exit_status
from utils import check_project_name, project_exists, load_model, save_model, BAD_REPLY
from utils import revert_working_model_to_default, save_working_model_as_default, report_exception
from sim.optimize import optimize, saveoptimization, defaultoptimizations, defaultobjectives, defaultconstraints
from sim.dataio import fromjson, tojson

# route prefix: /api/analysis/optimization
optimization = Blueprint('optimization',  __name__, static_folder = '../static')

@optimization.route('/list')
@login_required
@check_project_name
@report_exception()
def getOptimizationParameters():
    """ retrieve list of optimizations defined by the user, with parameters """
    current_app.logger.debug("/api/analysis/optimization/list")
    # get project name
    project_name = request.project_name
    project_id = request.project_id
    if not project_exists(project_id):
        reply = BAD_REPLY
        reply['reason'] = 'Project %s:%s does not exist' % (project_id, project_name)
        return jsonify(reply)
    else:
        D = load_model(project_id)
        if not 'optimizations' in D:
            optimizations = defaultoptimizations(D)
        else:
            optimizations = D['optimizations']
        optimizations = tojson(optimizations)
        return json.dumps({'optimizations':optimizations})


@optimization.route('/start', methods=['POST'])
@login_required
@check_project_name
def startOptimization():
    """ Start optimization """
    data = json.loads(request.data)
    current_app.logger.debug("optimize: %s" % data)
    # get project name
    project_id = request.project_id
    project_name = request.project_name
    if not project_exists(project_id):
        reply = BAD_REPLY
        reply['reason'] = 'Project %s:%s does not exist' % (project_id, project_name)
        return jsonify(reply)
    try:
        can_start, can_join, current_calculation = start_or_report_calculation(current_user.id, project_id, optimize, db.session)
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
            CalculatingThread(db.engine, current_user, project_id, timelimit, numiter, optimize, args, with_stoppingfunc = True).start()
            msg = "Starting optimization thread for user %s project %s:%s" % (current_user.name, project_id, project_name)
            current_app.logger.debug(msg)
            return json.dumps({"status":"OK", "result": msg, "join":True})
        else:
            msg = "Thread for user %s project %s:%s (%s) has already started" % (current_user.name, project_id, project_name, current_calculation)
            return json.dumps({"status":"OK", "result": msg, "join":can_join})
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})

@optimization.route('/stop')
@login_required
@check_project_name
def stopCalibration():
    """ Stops calibration """
    project_id = request.project_id
    project_name = request.project_name
    cancel_calculation(current_user.id, project_id, optimize, db.session)
    return json.dumps({"status":"OK", "result": "optimize calculation for user %s project %s:%s requested to stop" \
        % (current_user.name, project_id, project_name)})

@optimization.route('/working')
@login_required
@check_project_name
@report_exception()
def getWorkingModel():
    """ Returns the working model for optimization. """
    from flask import stream_with_context, request, Response
    import datetime
    import dateutil.tz
    from copy import deepcopy
    
    current_app.logger.debug("/api/optimization/working")
    result = {}
    D_dict = {}
    # Get optimization working data
    project_id = request.project_id
    project_name = request.project_name
    D_dict_new = load_model(project_id, working_model = False, from_json = False)
    new_optimizations = D_dict_new.get('optimizations')
    if not new_optimizations:
        D_new = fromjson(D_dict_new)
        new_optimizations = tojson(defaultoptimizations(D_new))
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
            status = 'NOK'

    if status!='NOK': D_dict = load_model(project_id, working_model = True, from_json = False)

    optimizations = D_dict.get('optimizations')
    names = [item['name'] for item in optimizations] if optimizations else ['Default']
    current_app.logger.debug("optimization names: %s" % names)
    is_dirty = False
    for new_index, optimization in enumerate(new_optimizations):
        #trying to update the results in the current model with the available results from the working model
        name = optimization['name']
        if optimizations and name in names:
            index = names.index(name)
            if ('result' in optimizations[index]) and (optimization.get('result')!=optimizations[index]['result']):
                new_optimizations[new_index] = deepcopy(optimizations[index])
                #warn that these results are transient
                is_dirty = True
    result['optimizations'] = new_optimizations
    result['status'] = status
    result['dirty'] = is_dirty
    if error_text:
        result['exception'] = error_text
    return jsonify(result)


@optimization.route('/save', methods=['POST'])
@login_required
@check_project_name
@report_exception()
def saveModel():
    from sim.optimize import saveoptimization
    """ Saves working model as the default model """
    reply = BAD_REPLY

    # get project name
    project_id = request.project_id
    project_name = request.project_name
    if not project_exists(project_id):
        reply['reason'] = 'Project %s:%s does not exist' % (project_id, project_name)
    else:
        # now, save the working model, read results and save for the optimization with the given name
        D_dict = save_working_model_as_default(project_id)

        reply['optimizations'] = D_dict['optimizations']
        reply['status']='OK'
    return jsonify(reply)

@optimization.route('/revert', methods=['POST'])
@login_required
@check_project_name
@report_exception()
def revertCalibrationModel():
    """ Revert working model to the default model """
    reply = BAD_REPLY

    # get project name
    project_id = request.project_id
    if not project_exists(project_id):
        reply['reason'] = 'Project %s does not exist' % project_id
    else:
        D_dict = revert_working_model_to_default(project_id)
        D = fromjson(D_dict)
        reply['optimizations'] = D_dict.get('optimizations') or tojson(defaultoptimizations(D))
        reply['status']='OK'
    return jsonify(reply)


@optimization.route('/remove/<name>', methods=['POST'])
@login_required
@check_project_name
@report_exception()
def removeOptimizationSet(name):
    """ Removes given optimization from the optimization set """
    from sim.optimize import removeoptimization
    reply = BAD_REPLY

    # get project name
    project_id = request.project_id
    if not project_exists(project_id):
        reply['reason'] = 'Project %s does not exist' % project_id
    else:
        D = load_model(project_id, from_json = True)
        D = removeoptimization(D, name)
        D_dict = tojson(D)
        save_model(project_id, D_dict)
        reply['status']='OK'
        reply['name'] = 'deleted'
        reply['optimizations'] = D_dict['optimizations']
    return jsonify(reply)

@optimization.route('/create', methods=['POST'])
@login_required
@check_project_name
@report_exception()
def create_optimization():
    """ Creates a new optimization from the optimization set """

    reply = BAD_REPLY
    data = json.loads(request.data)

    name = data.get('name')
    if not name:
        reply['reason'] = 'Please provide a name for new optimization'
        return jsonify(reply)

    # get project name
    project_id = request.project_id
    if not project_exists(project_id):
        reply['reason'] = 'Project %s does not exist' % project_id
    else:
        D = load_model(project_id, from_json = True)
        objectives = data.get('objectives')
        if objectives:
            objectives = fromjson( objectives )
        else:
            objectives = defaultobjectives(D)
        constraints = data.get('constraints')
        if constraints:
            constraints = fromjson( constraints )
        else:
            constraints = defaultconstraints(D)

        #save new optimization slot
        D = saveoptimization(D, name, objectives, constraints)
        D_dict = tojson(D)
        save_model(project_id, D_dict)
        #return all available optimizations back
        reply['status']='OK'
        reply['optimizations'] = D_dict['optimizations']
    return jsonify(reply)
