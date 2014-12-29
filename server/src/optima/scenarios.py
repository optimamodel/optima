from flask import Blueprint, request, jsonify, helpers, current_app
import json
import traceback
from sim.optimize import optimize
from sim.bunch import unbunchify
from sim.bunch import bunchify
from sim.scenarios import runscenarios
from utils import load_model, save_model, project_exists, check_project_name, report_exception
from flask.ext.login import login_required, current_user
from dbconn import db
from dbmodels import ProjectDb, WorkingProjectDb


""" route prefix: /api/analysis/scenarios """
scenarios = Blueprint('scenarios',  __name__, static_folder = '../static')
scenarios.config = {}

@scenarios.record
def record_params(setup_state):
  app = setup_state.app
  scenarios.config = dict([(key,value) for (key,value) in app.config.iteritems()])


@scenarios.route('/params')
@login_required
@check_project_name
@report_exception()
def get_scenario_params():
    from sim.parameters import parameters
    from sim.scenarios import getparvalues
    scenario_params = parameters()
    real_params = []
    user_id = current_user.id
    proj = ProjectDb.query.filter_by(user_id=user_id, name=request.project_name).first()
    D = bunchify(proj.model)
    db.session.close()
    pops_short = [item['short_name'] for item in proj.populations]

    for param in scenario_params:
        if not param['modifiable']: continue
        item = bunchify({'names':param['keys'], 'pops':0, 'startyear':proj.datastart, 'endyear':proj.dataend})
        val_pair = None
        try:
            val_pair = getparvalues(D, item)
            param['values'] = val_pair
            real_params.append(param)
        except:
            continue

    current_app.logger.debug("real_params:%s" % real_params)
    return json.dumps({"params":real_params})

"""
Returns a list of scenarios defined by the user, or the default scenario list
"""
@scenarios.route('/list')
@login_required
@check_project_name
@report_exception()
def list():
    from sim.scenarios import defaultscenarios
    current_app.logger.debug("/api/analysis/scenarios/list")
    # get project name
    project_name = request.project_name
    if not project_exists(project_name):
        reply['reason'] = 'Project %s does not exist' % project_name
        return reply
    D = load_model(project_name)
    if not 'scens' in D:
        scenarios = defaultscenarios(D)
    else:
        scenarios = [item.scenario for item in D.scens]
    scenarios = unbunchify(scenarios)
    return json.dumps({'scenarios':scenarios})


"""
Gets a list of scenarios defined by the user, produces graphs out of them and sends back
"""
@scenarios.route('/run', methods=['POST'])
@login_required
@check_project_name
def runScenarios():
    data = json.loads(request.data)
    current_app.logger.debug("/api/analysis/scenarios/run %s" % data)
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
            current_app.logger.debug("model: %s" % project_name)
            save_model(project_name, D_dict)
    except Exception, err:
        var = traceback.format_exc()
        return jsonify({"status":"NOK", "exception":var})
    return jsonify(D_dict.get('plot',{}).get('scens',{}))
