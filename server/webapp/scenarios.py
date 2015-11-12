from flask import Blueprint, request, jsonify, current_app
import json
import traceback
from sim.dataio import tojson, fromjson
from sim.scenarios import runscenarios
from webapp.utils import load_model, save_model, check_project_exists, check_project_name, report_exception, load_project
from flask.ext.login import login_required # pylint: disable=E0611,F0401

# route prefix: /api/analysis/scenarios
scenarios = Blueprint('scenarios',  __name__, static_folder = '../static')
scenarios.config = {}

@scenarios.record
def record_params(setup_state):
    app = setup_state.app
    scenarios.config = dict([(key,value) for (key,value) in app.config.iteritems()])


@scenarios.route('/parameters')
@login_required
@check_project_name
@report_exception()
def get_scenario_parameters():
    from sim.parameters import parameters
    from sim.scenarios import getparvalues
    scenario_params = parameters()
    real_parameters = []
    project = load_project(request.project_id)
    D = fromjson(project.model)

    for parameter in scenario_params:
        if not parameter['modifiable']: continue
        item = fromjson({'names':parameter['keys'], 'pops':0, \
            'startyear':project.datastart, 'endyear':project.dataend})
        val_pair = None
        try:
            val_pair = getparvalues(D, item)
            parameter['values'] = val_pair
            real_parameters.append(parameter)
        except: # pylint: disable=bare-except
            continue

    current_app.logger.debug("real_parameters:%s" % real_parameters)
    return jsonify({"parameters":real_parameters})

@scenarios.route('/list')
@login_required
@check_project_name
@check_project_exists
@report_exception()
def list_scenarios():
    """
    Returns a list of scenarios defined by the user, or the default scenario list

    """
    from sim.scenarios import defaultscenarios
    current_app.logger.debug("/api/analysis/scenarios/list")
    # get project name
    project_id = request.project_id
    D = load_model(project_id)
    if not 'scens' in D:
        the_scenarios = defaultscenarios(D)
    else:
        the_scenarios = [item['scenario'] for item in D['scens']]
    the_scenarios = tojson(the_scenarios)
    return jsonify({'scenarios':the_scenarios})

@scenarios.route('/run', methods=['POST'])
@login_required
@check_project_name
@check_project_exists
def runScenarios():
    """
    Gets a list of scenarios defined by the user, produces graphs out of them
    and sends back.

    """
    data = json.loads(request.data)
    current_app.logger.debug("/api/analysis/scenarios/run %s" % data)
    # get project name
    project_id = request.project_id

    #expects json: {"scenarios":[scenariolist]} and gets project_name from session
    args = {}
    the_scenarios = data.get("scenarios")
    if the_scenarios:
        args["scenariolist"] = fromjson(the_scenarios)
    dosave = data.get("dosave")
    try:
        D = load_model(project_id)
        args['D'] = D
        D = runscenarios(**args)
        D_dict = tojson(D)
        if dosave:
            current_app.logger.debug("model: %s" % project_id)
            save_model(project_id, D_dict)
    except Exception:
        var = traceback.format_exc()
        return jsonify({"exception":var}), 500
    return jsonify(D_dict.get('plot',{}).get('scens',{}))
