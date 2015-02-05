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
from flask import request, jsonify, Blueprint, current_app
from dbconn import db
from async_calculate import CalculatingThread, start_or_report_calculation, cancel_calculation, check_calculation
from async_calculate import check_calculation_status, good_exit_status
from utils import check_project_name, project_exists, load_model, save_model, \
revert_working_model_to_default, save_working_model_as_default, report_exception
from sim.optimize import optimize
from sim.optimize import add_optimization
from sim.optimize import defaultoptimizations
from sim.bunch import bunchify, unbunchify
import json
import traceback
from flask.ext.login import login_required, current_user

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
        reply['reason'] = 'Project %s does not exist' % project_id
        return reply
    D = load_model(project_id)
    if not 'optimizations' in D:
        optimizations = defaultoptimizations(D)
    else:
        optimizations = D.optimizations
    optimizations = unbunchify(optimizations)
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
        from utils import BAD_REPLY
        reply = BAD_REPLY
        reply['reason'] = 'File for project %s does not exist' % project_id
        return jsonify(reply)
    try:
        can_start, can_join, current_calculation = start_or_report_calculation(current_user.id, project_id, optimize, db.session)
        if can_start:
            # Prepare arguments
            args = {'verbose':2}
            objectives = data.get('objectives')
            if objectives:
                args['objectives'] = bunchify( objectives )
            constraints = data.get('constraints')
            if constraints:
                args['constraints'] = bunchify( constraints )
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
    D_dict = {}
    # Get optimization working data
    project_id = request.project_id
    project_name = request.project_name
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
    if status!='NOK': D_dict = load_model(project_id, working_model = True, as_bunch = False)

    result = {}

    result['optimizations'] = unbunchify(D_dict.get('optimizations'))
    result['status'] = status
    if error_text:
        result['exception'] = error_text
    return jsonify(result)


@optimization.route('/save', methods=['POST'])
@login_required
@check_project_name
def saveModel():
    from sim.optimize import saveoptimization
    """ Saves working model as the default model """
    reply = {'status':'NOK'}

    # get project name
    project_id = request.project_id
    if not project_exists(project_id):
        reply['reason'] = 'File for project %s does not exist' % project_id
        return jsonify(reply)

    try:
        # now, save the working model, read results and save for the optimization with the given name
        D_dict = save_working_model_as_default(project_id)

        reply['status']='OK'
        reply['optimizations'] = D_dict['optimizations']
        return jsonify(reply)
    except Exception, err:
        reply['exception'] = traceback.format_exc()
        return jsonify(reply)

@optimization.route('/revert', methods=['POST'])
@login_required
@check_project_name
def revertCalibrationModel():
    """ Revert working model to the default model """
    reply = {'status':'NOK'}

    # get project name
    project_id = request.project_id
    if not project_exists(project_id):
        reply['reason'] = 'File for project %s does not exist' % project_id
        return jsonify(reply)
    try:
        revert_working_model_to_default(project_id)
        return jsonify({"status":"OK"})
    except Exception, err:
        reply['exception'] = traceback.format_exc()
        return jsonify(reply)


@optimization.route('/remove/<name>', methods=['POST'])
@login_required
@check_project_name
def removeOptimizationSet(name):
    """ Removes given optimization from the optimization set """
    from sim.optimize import removeoptimization
    reply = {'status':'NOK'}

    # get project name
    project_id = request.project_id
    if not project_exists(project_id):
        reply['reason'] = 'File for project %s does not exist' % project_id
        return jsonify(reply)
    else:
        D = load_model(project_id, as_bunch = True)
        D = removeoptimization(D, name)
        D_dict = D.toDict()
        save_model(project_id, D_dict)
        reply['status']='OK'
        reply['name'] = 'deleted'
        reply['optimizations'] = D_dict['optimizations']
        return jsonify(reply)

@optimization.route('/create', methods=['POST'])
@login_required
@check_project_name
def create_optimization():
    """ Creates a new optimization from the optimization set """

    reply = {'status':'NOK'}
    data = json.loads(request.data)

    name = data.get('name')
    if not name:
        reply['reason'] = 'Please provided a name'
        return jsonify(reply)

    # get project name
    project_id = request.project_id
    if not project_exists(project_id):
        reply['reason'] = 'Project %s does not exist' % project_id
        return jsonify(reply)
    else:
        D = load_model(project_id, as_bunch = True)
        D, optimization = add_optimization(D, name)
        if not optimization:
            reply['reason'] = 'The provided optimization name already exists'
            return jsonify(reply)
        D_dict = D.toDict()
        save_model(project_id, D_dict)
        reply['status']='OK'
        reply['optimization'] = optimization
        return jsonify(reply)
