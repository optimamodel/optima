from flask import Blueprint, request, jsonify
import json
import traceback
from sim.optimize import optimize
from sim.bunch import unbunchify
from sim.scenarios import runscenarios
from utils import load_model, save_model, project_exists, check_project_name
from flask.ext.login import login_required

""" route prefix: /api/analysis """
analysis = Blueprint('analysis',  __name__, static_folder = '../static')
analysis.config = {}

@analysis.record
def record_params(setup_state):
  app = setup_state.app
  analysis.config = dict([(key,value) for (key,value) in app.config.iteritems()])

"""
Gets a list of scenarios defined by the user, produces graphs out of them and sends back
"""
@analysis.route('/scenarios/run', methods=['POST'])
@login_required
@check_project_name
def runScenarios():
    data = json.loads(request.data)
    print("/api/analysis/run %s" % data)
    # get project name
    project_name = request.project_name
    if not project_exists(project_name):
        reply['reason'] = 'Project %s does not exist' % project_name

    #expects json: {"scenarios":[scenariolist]} and gets project_name from session
    args = {}
    scenarios = data.get("scenarios")
    if scenarios:
        args["scenarios"] = bunchify(scenarios)
    dosave = data.get("dosave")
    try:
        D = load_model(project_name)
        args['D'] = D
        D = runscenarios(**args) 
        D_dict = D.toDict()
        if dosave:
            print("model: %s" % project_name)
            save_model(project_name, D_dict)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify(D_dict.get('plot',{}).get('E',{}))


"""
Defines optimisation objectives from the data collected on the frontend.
"""
@analysis.route('/optimisation/define/<defineType>', methods=['POST'])
@login_required
@check_project_name
def defineObjectives(defineType):
    data = json.loads(request.data)
#   TODO: how to save these data in the model?
#    json_file = os.path.join(analysis.config['UPLOAD_FOLDER'], "optimisation.json")
#    with open(json_file, 'w') as outfile:
#        json.dump(data, outfile)
    return json.dumps({'status':'OK'})

"""
Starts optimisation for the current model. Gives back line plot and two pie plots.
"""
@analysis.route('/optimisation/start')
@login_required
@check_project_name
def runOptimisation():
    # should call method in optimize.py but it's not implemented yet. for now just returns back the file
    reply = {'status':'NOK'}
    
    # get project name
    project_name = request.project_name
    if not project_exists(project_name):
        reply['reason'] = 'Project %s does not exist' % project_name
        return jsonify(reply)
#    json_file = os.path.join(analysis.config['UPLOAD_FOLDER'], "optimisation.json")
#    if (not os.path.exists(json_file)):
#        reply["reason"] = "Define the optimisation objectives first"
#        return jsonify(reply)
    try:
        print("about to load model for project %s ..." % project_name)
        D = load_model(project_name)
        (lineplot, dataplot) = optimize(D)
        (lineplot, dataplot) = (unbunchify(lineplot), unbunchify(dataplot))
        return json.dumps({"lineplot":lineplot, "dataplot":dataplot})
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify(D_dict.get('O',{}))


