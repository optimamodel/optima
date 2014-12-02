from flask import Blueprint, request, jsonify, helpers
import json
import traceback
from sim.optimize import optimize
from sim.bunch import unbunchify
from sim.bunch import bunchify
from sim.scenarios import runscenarios
from utils import load_model, save_model, project_exists, check_project_name
from flask.ext.login import login_required

""" route prefix: /api/analysis/scenarios """
scenarios = Blueprint('scenarios',  __name__, static_folder = '../static')
scenarios.config = {}

scenario_params_file_name = "scenario_params.csv"


@scenarios.record
def record_params(setup_state):
  app = setup_state.app
  scenarios.config = dict([(key,value) for (key,value) in app.config.iteritems()])


@scenarios.route('/params')
@login_required
def get_scenario_params():
    scenario_params_file_path = helpers.safe_join(scenarios.static_folder, scenario_params_file_name)
    f = open(scenario_params_file_path, "rU")
    if not f:
        reply['reason'] = 'Scenario params file %s does not exist' % scenario_params_file_path
        return reply
    lines = [l.strip() for l in f.readlines()][1:]
    split_lines = [l.split(';') for l in lines]
    scenario_params = [{'keys':r[0].replace('[:]','').split('.')[1:],'name':r[2]} for r in split_lines]
    return json.dumps({"params":scenario_params})

"""
Gets a list of scenarios defined by the user, produces graphs out of them and sends back
"""
@scenarios.route('/run', methods=['POST'])
@login_required
@check_project_name
def runScenarios():
    data = json.loads(request.data)
    print("/api/analysis/scenarios/run %s" % data)
    # get project name
    project_name = request.project_name
    if not project_exists(project_name):
        reply['reason'] = 'Project %s does not exist' % project_name
        return reply

    #expects json: {"scenarios":[scenariolist]} and gets project_name from session
    args = {}
    scenarios = data.get("scenarios")
    if scenarios:
        args["scenariolist"] = bunchify(scenarios)
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
    return jsonify(D_dict.get('plot',{}).get('scens',{}))
