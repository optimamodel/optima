import json
import uuid
import re

import mpld3

from flask import current_app, request

from flask.ext.login import login_required
from flask_restful import Resource, marshal_with, fields
from flask_restful_swagger import swagger
from flask import helpers

from server.webapp.inputs import SubParser, scenario_par, scenario_program, Json as JsonInput
from server.webapp.dataio import TEMPLATEDIR, upload_dir_user
from server.webapp.utils import (
    load_project_record, load_progset_record, load_program_record, load_scenario_record, RequestParser, report_exception, modify_program_record)
from server.webapp.exceptions import ProjectDoesNotExist, ProgsetDoesNotExist, ProgramDoesNotExist, ScenarioDoesNotExist
from server.webapp.resources.common import file_resource, file_upload_form_parser
from server.webapp.dbconn import db
from server.webapp.dbmodels import ScenariosDb

import optima as op

scenario_parser = RequestParser()
scenario_parser.add_arguments({
    'name': {'type': str, 'location': 'args', 'required': True},
    'parset_id': {'type': uuid.UUID, 'location': 'args', 'required': True},
    'progset_id': {'type': uuid.UUID, 'location': 'args', 'required': True},
    'scenario_type': {'type': str, 'location': 'args', 'required': True},
    'active': {'type': bool, 'location': 'args', 'required': True}
})

scenario_list_scenario_parser = RequestParser()
scenario_list_scenario_parser.add_arguments({
    'id': {'required': False, 'location': 'json'},
    'name': {'type': str, 'required': True, 'location': 'json'},
    'parset_id': {'required': True, 'location': 'json'},
    'progset_id': {'type': uuid.UUID, 'location': 'json', 'required': True},
    'scenario_type': {'type': str, 'required': True, 'location': 'json'},
    'active': {'type': bool, 'required': True, 'location': 'json'},
    'pars': {'type': scenario_par, 'required': False, 'location': 'json'},  # only for Paramscen
    'years': {'type': list, 'required': False, 'location': 'json'}, # only for Budgetscen /Coveragescen
    'budget': {'type': scenario_program, 'required': False, 'location': 'json'}, # only for Budgetscen
    'coverage': {'type': scenario_program, 'required': False, 'location': 'json'}, # only for Coveragescen
})

scenario_list_parser = RequestParser()
scenario_list_parser.add_arguments({
    'scenarios': {
        'type': SubParser(scenario_list_scenario_parser),
        # 'type': JsonInput,
        'action': 'append',
        'required': False,
        'default': []
    },
})


def check_pars(blob, raise_exception = True):
    """
    Check the pars attribute for scenarios.
    """
    pars = []

    if 'pars' not in blob.keys():
        if raise_exception:
            raise ValueError("JSON body requires 'pars' parameter")
        else:
            return pars

    if not isinstance(blob['pars'], list):
        raise ValueError("'pars' needs to be a list.")

    for i in blob['pars']:

        pars.append({
            'endval': int(i['endval']),
            'endyear': int(i['endyear']),
            'name': str(i['name']),
            'for': list(i['for']),
            'startval': int(i['startval']),
            'startyear': int(i['startyear'])
        })

    return pars


def check_program(blob, key): # result is either budget or coverage, depending on scenario type
    from server.webapp.inputs import scenario_program
    programs = {}
    if key not in blob.keys():
        return programs

    orig_programs = blob[key]
    return scenario_program(orig_programs)


# /api/project/<project-id>/scenarios


class Scenarios(Resource):
    """
    Scenarios for a given project.
    """
    method_decorators = [report_exception, login_required]

    def _scenarios_for_fe(self, scenarios):
        rv = []
        for scenario in scenarios:
            print "scenario", scenario.blob
            if 'pars' in scenario.blob:
                pars = []
                for par in scenario.blob['pars']:
                    par['for'] = par['for'][0]
                    pars.append(par)
                scenario.blob['pars'] = pars

            for key in ['budget', 'coverage']:
                if key in scenario.blob:
                    item_list = []
                    for k, v in scenario.blob[key].iteritems():
                        item = {
                            'program': k,
                            'values': v
                        }
                        item_list.append(item)
                    scenario.blob[key] = item_list

            rv.append(scenario)
        print "rv", rv
        return rv

    @swagger.operation()
    @marshal_with(ScenariosDb.resource_fields, envelope='scenarios')
    def get(self, project_id):
        """
        Get the scenarios for the given project
        """
        project_entry = load_project_record(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        reply = db.session.query(ScenariosDb).filter_by(project_id=project_entry.id).all()
        return self._scenarios_for_fe(reply)

    @swagger.operation(
        parameters=scenario_parser.swagger_parameters(),
        notes="""
            Create a new scenario.

            If it is a Parameter scenario, the request body should be a JSON
            dict with the 'pars' key.
        """
    )
    @marshal_with(ScenariosDb.resource_fields)
    def post(self, project_id):
        """
        Create a new scenario for the given project.
        """
        args = scenario_parser.parse_args()

        if args.get('scenario_type') not in ["parameter", "budget", "coverage"]:
            raise ValueError("Type needs to be 'parameter', 'budget' or 'coverage'.")

        blob = {}
        data = json.loads(request.data)
        pars = check_pars(data, raise_exception = (args['scenario_type'] == "parameter"))
        budget = check_program(data, 'budget')
        coverage = check_program(data, 'coverage')
        if pars:
            blob['pars'] = pars
        if budget:
            blob['budget'] = budget
        if coverage:
            blob['coverage'] = coverage

        scenario_entry = ScenariosDb(project_id, blob=blob, **args)

        db.session.add(scenario_entry)
        db.session.flush()
        db.session.commit()

        return scenario_entry, 201

    def _upsert_scenario(self, project_id, id, **kwargs):
        pars = kwargs.pop('pars', None)
        budget = kwargs.pop('budget', None)
        coverage = kwargs.pop('coverage', None)
        years = kwargs.pop('years', None)
        print "years", years
        if years:
            years = [int(y) for y in years]
        print "years", years

        blob = {}
        if pars:
            blob['pars'] = pars
        if budget:
            blob['budget'] = budget
        if coverage:
            blob['coverage'] = coverage
        if years:
            blob['years'] = years

        scenario_entry = None
        if id is not None:
            scenario_entry = ScenariosDb.query.filter_by(id=id).first()
            scenario_entry.blob = blob
        if not scenario_entry:
            scenario_entry = ScenariosDb(project_id, blob=blob, **kwargs)
        else:
            for key, value in kwargs.iteritems():
                setattr(scenario_entry, key, value)

        db.session.add(scenario_entry)
        db.session.flush()
        db.session.commit()

    @swagger.operation(
        parameters=scenario_list_parser.swagger_parameters(),
        responseClass=ScenariosDb.__name__
    )
    @marshal_with(ScenariosDb.resource_fields, envelope='scenarios')
    def put(self, project_id):
        args = scenario_list_parser.parse_args()

        scenarios = args['scenarios']

        db.session.query(ScenariosDb).filter_by(project_id=project_id).filter(
            ~ScenariosDb.id.in_([scenario['id'] for scenario in scenarios if 'id' in scenario and scenario['id']])
        ).delete(synchronize_session='fetch')
        db.session.flush()

        for scenario in scenarios:
            self._upsert_scenario(project_id, **scenario)
        db.session.commit()

        return self._scenarios_for_fe(ScenariosDb.query.filter_by(project_id=project_id).all())



def extract_graph_selector(graph_key):
    s = repr(graph_key)
    base = "".join(re.findall("[a-zA-Z]+", s.split(",")[0]))
    if "'t'" in s:
        suffix = "-tot"
    elif "'p'" in s:
        suffix = "-per"
    else:
        suffix = ""
    return base + suffix



def make_mpld3_graph_dict(result, which=None):
    """
    Converts an Optima sim Result into a dictionary containing
    mpld3 graph dictionaries and associated keys for display,
    which can be exported as JSON.

    Args:
        result: the Optima simulation Result object
        which: a list of keys to determine which plots to generate

    Returns:
        A dictionary of the form:
            { "graphs": {
                "mpld3_graphs": [<mpld3 graph dictioanry>...],
                "graph_selectors": ["key of a selector",...],
                "selectors": [<selector dictionary>]
            }
            - mpld3_graphs is the same length as graph_selectors
            - selectors are shown on screen and graph_selectors refer to selectors
            - selector: {
                "key": "unique name",
                "name": "Long description",
                "checked": boolean
              }
        }
    """

    graph_selectors = op.getplotselections(result)
    keys = graph_selectors['keys']
    names = graph_selectors['names']
    checks = graph_selectors['defaults']
    selectors = [
        {'key': key, 'name': name, 'checked': checked}
         for (key, name, checked) in zip(keys, names, checks)]

    if which is None:
        which = [s["key"] for s in selectors if s["checked"]]
    which = keys
    graphs = op.plotting.makeplots(result, toplot=which, figsize=(4, 3))

    graph_selectors = []
    mpld3_graphs = []
    for graph_key in graphs:
        # Add necessary plugins here
        mpld3.plugins.connect(
            graphs[graph_key],
            mpld3.plugins.MousePosition(fontsize=14, fmt='.4r'))

        mpld3_dict = mpld3.fig_to_dict(graphs[graph_key])

        # a hack to get rid of NaNs, javascript JSON parser doesn't like them
        mpld3_dict = json.loads(json.dumps(mpld3_dict, cls=Op).replace('NaN', 'null'))

        graph_selectors.append(extract_graph_selector(graph_key))
        mpld3_graphs.append(mpld3_dict)

    return {
        'graphs': {
            "mpld3_graphs": mpld3_graphs,
            "selectors": selectors,
            'graph_selectors': graph_selectors
        }
    }



# /api/project/<project-id>/scenarios/results

class ScenarioResults(Resource):

    method_decorators = [report_exception, login_required]

    @swagger.operation()
    def get(self, project_id):
        """
        Run the scenarios for a given project and returns the graphs.
        """
        project_entry = load_project_record(project_id)
        project = project_entry.hydrate()
        project.runscenarios()
        return make_mpld3_graph_dict(project.results[-1])



# /api/project/<project-id>/scenarios/<scenarios-id>
class Scenario(Resource):
    """
    A given scenario.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation()
    @marshal_with(ScenariosDb.resource_fields)
    def get(self, project_id, scenario_id):
        """
        Get a given single scenario.
        """
        return load_scenario_record(project_id, scenario_id)

    @swagger.operation(
        parameters=scenario_parser.swagger_parameters(),
        notes="""
            Update an existing scenario.

            If it is a Parameter scenario, the request body should be a JSON
            dict with the 'pars' key.
        """
    )
    @marshal_with(ScenariosDb.resource_fields)
    def put(self, project_id, scenario_id):
        """
        Update the given single scenario.
        """
        args = scenario_parser.parse_args()

        pars = check_pars(data, raise_exception = (args['scenario_type'] == "Parameter"))
        budget = check_program(data, 'budget')
        coverage = check_program(data, 'coverage')
        if pars:
            blob['pars'] = pars
        if budget:
            blob['budget'] = budget
        if coverage:
            blob['coverage'] = coverage

        scenario_entry = load_scenario_record(project_id, scenario_id)

        scenario_entry.name = args['name']
        scenario_entry.scenario_type = args['scenario_type']
        scenario_entry.parset_id = args['parset_id']
        scenario_entry.progset_id = args.get('progset_id')
        scenario_entry.active = args['active']
        scenario_entry.blob = blob

        db.session.commit()

        return scenario_entry

    @swagger.operation()
    def delete(self, project_id, scenario_id):
        """
        Delete the given scenario.
        """
        scenario_entry = load_scenario_record(project_id, scenario_id)

        db.session.delete(scenario_entry)
        db.session.commit()

        return b'', 204
