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
from utils import check_project_name, project_exists, pick_params, is_model_calibrating, set_working_model_calibration, load_model, save_working_model
from sim.optimize import optimize
from sim.bunch import bunchify
import json
import traceback

# route prefix: /api/optimization
optimization = Blueprint('optimization',  __name__, static_folder = '../static')

""" 
Start optimization 
"""
@optimization.route('/start', methods=['POST'])
@login_required
@check_project_name
def startOptimization():
    reply = {'status':'NOK'}
    data = json.loads(request.data)
    
    # get project name 
    project_name = request.project_name
    D = None
    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % project_name
        return jsonify(reply)
    try:
        D = load_model(project_name)

        # Prepare arguments
        args = {}

        objectives = data.get('objectives')
        if objectives:
            args['objectives'] = bunchify( objectives )

        constraints = data.get('constraints')
        if constraints:
            args['constraints'] = bunchify( constraints )

        #timelimit = data.get("timelimit")
        timelimit = 60
        if timelimit:
            timelimit = int(timelimit) / 5
            args["timelimit"] = 5
        if is_model_calibrating(request.project_name):
            return jsonify({"status":"NOK", "reason":"calibration already going"})
        else:
            # We are going to start calibration
            set_working_model_calibration(project_name, True)
            
            # Do calculations 5 seconds at a time and then save them
            # to db.
            for i in range(0, timelimit):
                
                # Make sure we are still calibrating
                if is_model_calibrating(request.project_name):
                    D = optimize(D, **args)
                    D_dict = D.toDict()
                    save_working_model(project_name, D_dict)
                else:
                    break
            
    except Exception, err:
        set_working_model_calibration(project_name, False)
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
        
    set_working_model_calibration(project_name, False)
    return jsonify(D_dict.get('plot',{}).get('E',{}))