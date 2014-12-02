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
from flask import request, jsonify, Blueprint
from flask.ext.login import login_required
from dbconn import db
from async_calculate import CalculatingThread, sentinel
from utils import check_project_name, project_exists, pick_params, load_model, save_working_model, report_exception
from sim.optimize import optimize
from sim.bunch import bunchify
import json
import traceback
from flask.ext.login import login_required, current_user

# route prefix: /api/analysis/optimization
optimization = Blueprint('optimization',  __name__, static_folder = '../static')

def get_optimization_results(D_dict):
    return {'graph': D_dict.get('plot',{}).get('OM',{}), 'pie':D_dict.get('plot',{}).get('OA',{})}

"""
Start optimization
"""
@optimization.route('/start', methods=['POST'])
@login_required
@check_project_name
def startOptimization():
    data = json.loads(request.data)

    # get project name
    project_name = request.project_name
    D = None
    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % project_name
        return jsonify(reply)
    try:
        if not project_name in sentinel['projects'] or not sentinel['projects'][project_name]:
            # Prepare arguments
            args = {}
            objectives = data.get('objectives')
            if objectives:
                args['objectives'] = bunchify( objectives )
            constraints = data.get('constraints')
            if constraints:
                args['constraints'] = bunchify( constraints )
            timelimit = int(data.get("timelimit")) # for the thread
            args["timelimit"] = 10 # for the autocalibrate function
            CalculatingThread(db.engine, sentinel, current_user, project_name, timelimit, optimize, args).start()
            msg = "Starting optimization thread for user %s project %s" % (current_user.name, project_name)
            print(msg)
            return json.dumps({"status":"OK", "result": msg, "join":True})
        else:
            current_calculation = sentinel['projects'][project_name]
            print('sentinel object: %s' % sentinel)
            msg = "Thread for user %s project %s (%s) has already started" % (current_user.name, project_name, current_calculation)
            can_join = current_calculation==optimize.__name__
            return json.dumps({"status":"OK", "result": msg, "join":can_join})
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})

"""
Stops calibration
"""
@optimization.route('/stop')
@login_required
@check_project_name
def stopCalibration():
    prj_name = request.project_name
    if prj_name in sentinel['projects']:
        sentinel['projects'][prj_name] = False
    return json.dumps({"status":"OK", "result": "thread for user %s project %s stopped" % (current_user.name, prj_name)})


"""
Returns the working model for optimization.
"""
@optimization.route('/working')
@login_required
@check_project_name
@report_exception()
def getWorkingModel():
    from utils import BAD_REPLY
    from sim.optimize import optimize

    reply = BAD_REPLY
    # Get optimization working data
    prj_name = request.project_name
    if prj_name in sentinel['projects'] and sentinel['projects'][prj_name]==optimize.__name__:
        D_dict = load_model(prj_name, working_model = True, as_bunch = False)
        result = get_optimization_results(D_dict)
        result['status'] = 'Running'
    else:
        print("no longer optimizing")
        result['status'] = 'Done'
    return jsonify(result)

"""
Saves working model as the default model
"""
@optimization.route('/save', methods=['POST'])
@login_required
@check_project_name
def saveModel():
    reply = {'status':'NOK'}

    # get project name
    project_name = request.project_name
    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % project_name
        return jsonify(reply)

    try:
        D_dict = save_working_model_as_default(project_name)
        return jsonify(get_optimization_results(D_dict))
    except Exception, err:
        reply['exception'] = traceback.format_exc()
        return jsonify(reply)


"""
Revert working model to the default model
"""
@optimization.route('/revert', methods=['POST'])
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
        return jsonify({"status":"OK"})
    except Exception, err:
        reply['exception'] = traceback.format_exc()
        return jsonify(reply)
