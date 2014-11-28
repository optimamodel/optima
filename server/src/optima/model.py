from flask import Blueprint, request, jsonify
import json
import traceback
from sim.manualfit import manualfit
from sim.autofit import autofit
from sim.bunch import bunchify
from sim.runsimulation import runsimulation
from sim.makeccocs import makecco, plotallcurves
from utils import load_model, save_model, save_working_model, save_working_model_as_default, revert_working_model_to_default, project_exists, pick_params, check_project_name, for_fe, set_working_model_calibration, is_model_calibrating
from flask.ext.login import login_required
from signal import *
import threading
import time
import sys

""" route prefix: /api/model """
model = Blueprint('model',  __name__, static_folder = '../static')
model.config = {}

POOL_TIME = 5 #Seconds

# variables that are accessible from anywhere
sentinel = {
    'exit': False, # This will stop all threads
    'projects': {} # This set will an item per projects name with the sentinel boolean
}

class CalculatingThread(threading.Thread):
    def __init__(self, sentinel, limit, user, project_name):
        super(CalculatingThread, self).__init__()
        self.limit = limit
        self.sentinel = sentinel
        self.user_name = user.name
        self.user_id = user.id
        self.project_name = project_name
        if not self.project_name in self.sentinel['projects']:
            self.sentinel['projects'][project_name] = {}
        self.sentinel['projects'][project_name] = True
        print("starting thread for user: %s" % self.user_name)

    def run(self):
        #just a demo that it can 
        from utils import load_model_user, save_model_user
        D = load_model_user(self.project_name, self.user_id)

        for i in range(self.limit):
            if not self.sentinel['exit'] and self.sentinel['projects'][self.project_name]:
                print("i=%s" %i)
                print("user: %s" % self.user_name)
                args = {'timelimit':5, 'startyear':2000,'endyear':2015}
                D = autofit(D, **args)
                save_model_user(self.project_name, self.user_id, D)
                time.sleep(1)
            else:
                print("stopping requested")
                sys.exit()
        print("thread stopped")
        self.sentinel['projects'][self.project_name] = False
        sys.exit()


def interrupt(*args):
    print("stopping all threads")
    sentinel['exit'] = True
    sys.exit()

for sig in (SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM):
    signal(sig, interrupt)
    

@model.route('/thread/cancel')
@login_required
@check_project_name
def doInterrupt():
    print("stopping thread")
    if request.project_name in sentinel['projects']:
        sentinel['projects'][request.project_name] = False
    return json.dumps({"status":"OK", "result": "thread for user %s project %s stopped" % (current_user.name, request.project_name)})

@model.route('/thread/start/<limit>')
@login_required
@check_project_name
def doStuffStart(limit):
    # Do initialisation stuff here
    # Create your thread
    msg = ""
    if not request.project_name in sentinel['projects'] \
    or not sentinel['projects'][request.project_name]:
        msg = "starting thread for user %s project %s" % (current_user.name, request.project_name)
        CalculatingThread(sentinel, int(limit), current_user, request.project_name).start()
    else:
        msg = "thread for user %s project %s has already started" % (current_user.name, request.project_name)
        print(msg)
    return json.dumps({"status":"OK", "result": msg})


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
    print('data: %s' % request.data)
    data = json.loads(request.data)

    # get project name 
    project_name = request.project_name
    D = None
    if not project_exists(project_name):
        reply['reason'] = 'File for project %s does not exist' % project_name
        return jsonify(reply)
    try:
        D = load_model(project_name)
        args = {}
        startyear = data.get("startyear")
        if startyear:
            args["startyear"] = int(startyear)
        endyear = data.get("endyear")
        if endyear:
            args["endyear"] = int(endyear)
        timelimit = data.get("timelimit")
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
                    D = autofit(D, **args)
                    D_dict = D.toDict()
                    save_working_model(project_name, D_dict)
                    time.sleep(1)
                else:
                    break
            
    except Exception, err:
        set_working_model_calibration(project_name, False)
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
        
    set_working_model_calibration(project_name, False)
    return jsonify(D_dict.get('plot',{}).get('E',{}))

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
            
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify(D_dict.get('plot',{}).get('E',{}))

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
            
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify(D_dict.get('plot',{}).get('E',{}))

""" 
Uses provided parameters to manually calibrate the model (update it with these data) 
TODO: do it with the project which is currently in scope
"""
@model.route('/calibrate/manual', methods=['POST'])
@login_required
@check_project_name
def doManualCalibration():
    data = json.loads(request.data)
    print("/api/model/calibrate/manual %s" % data)
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
            print("model: %s" % project_name)
            save_model(project_name, D_dict)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify(D_dict.get('plot',{}).get('E',{}))

"""
Stops calibration
"""
@model.route('/calibrate/stop')
@login_required
@check_project_name
def stopCalibration():
    set_working_model_calibration(request.project_name, False)
    result = {"status": "OK"}
    return jsonify(result)

"""
Returns the working model of project.
"""
@model.route('/working')
@login_required
@check_project_name
def getWorkingModel():
    # Make sure model is calibrating
    if is_model_calibrating(request.project_name):
        D = load_model(request.project_name, working_model = True)
        D_dict = D.toDict()
        result = jsonify(D_dict.get('plot',{}).get('E',{}))
    else:
        print("no longer calibrating")
        result = jsonify({'status': "OK"})
    return result

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
    print("getModelParameters: %s" % group)
    D_dict = load_model(request.project_name, as_bunch = False)
    the_group = D_dict.get(group, {})
    print("the_group: %s" % the_group)
    return json.dumps(the_group)


"""
Returns the parameters of the given model in the given group / subgroup/ project.
"""
@model.route('/parameters/<group>/<subgroup>')
@login_required
@check_project_name
def getModelSubParameters(group, subgroup):
    print("getModelSubParameters: %s %s" % (group, subgroup))
    D_dict = load_model(request.project_name, as_bunch = False)
    the_group = D_dict.get(group,{})
    the_subgroup = the_group.get(subgroup, {})
    print "result: %s" % the_subgroup
    return jsonify(the_subgroup)


"""
Sets the given group parameters for the given model.
"""
@model.route('/parameters/<group>', methods=['POST'])
@login_required
@check_project_name
def setModelParameters(group):
    data = json.loads(request.data)
    print("set parameters group: %s for data: %s" % (group, data))
    project_name = request.project_name
    try:
        D_dict = load_model(project_name, as_bunch = False)
        D_dict[group] = data
        save_model(project_name, D_dict)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})        
    print "D as dict: %s" % D_dict
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
        print ("D-dict F: %s" % D_dict['F'])
        save_model(request.project_name, D_dict)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify(D_dict.get('plot',{}).get('E',{}))
#    options = {
#        'cache_timeout': model.get_send_file_max_age(example_excel_file_name),
#        'conditional': True,
#        'attachment_filename': downloadName
#    }
#    return helpers.send_file(data_file_path, **options)


"""
Calls makecco with parameters supplied from frontend
"""
@model.route('/costcoverage', methods=['POST'])
@login_required
@check_project_name
def doCostCoverage():
    data = json.loads(request.data)
    args = {}
    args['D'] = load_model(request.project_name)
    args = pick_params(["progname", "ccparams", "coparams"], data, args)
    try:
        if not args.get('ccparams'):
            args['ccparams'] = [0.9, 0.2, 800000.0, 7e6]
        if not args.get('coparams'):
            args['coparams'] = []
        plotdata, plotdata_co, plotdata_cc, effectnames, D = plotallcurves(**args)
        if args.get('dosave'):
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
    args = {}
    args['D'] = load_model(request.project_name)
    args = pick_params(["progname", "effectname", "ccparams", "coparams"], data, args)
    try:
        if not args.get('ccparams'):
            args['ccparams'] = [0.9, 0.2, 800000.0, 7e6]
        if not args.get('coparams'):
            args['coparams'] = []
        if not args.get('effectname'):
            args['effectname'] = default_effectname
        args['effectname'] = args['effectname'][:3]
        plotdata, plotdata_co, storeparams = makecco(**args)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify({"status":"OK", "plotdata": for_fe(plotdata), \
        "plotdata_co": for_fe(plotdata_co), "effectname": args['effectname']})
