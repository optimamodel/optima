from flask.ext.restful import marshal

from server.webapp.plot import make_mpld3_graph_dict

__doc__ = """

dataio.py contains all the functions that fetch and saves optima objects to/from database
and the file system. These functions abstracts out the data i/o for the web-server
api calls.

function call pairs are load_*/save_* and refers to saving to database.

Database record variables should have suffix _record

Parsed data structures should have suffix _summary
"""


import os
from functools import partial
from uuid import UUID
import pprint

from flask import helpers, current_app, abort
from flask.ext.login import current_user

from server.webapp.dbconn import db
from server.webapp.dbmodels import ProjectDb, ResultsDb, WorkingProjectDb
from server.webapp.exceptions import (
    ProjectDoesNotExist, ProgsetDoesNotExist, ParsetDoesNotExist, ProgramDoesNotExist)
from server.webapp.utils import TEMPLATEDIR, upload_dir_user, normalize_obj
from server.webapp.parse import (
    parse_default_program_summaries, parse_parameters_of_parset_list, convert_pars_list,
    parse_parameters_from_progset_parset, revert_targetpars, parse_program_summary,
    revert_costcovdata, revert_ccopars, revert_pars_list,
)
from server.webapp.exceptions import ProjectDoesNotExist

import optima as op


def authenticate_current_user():
    current_app.logger.debug("authenticating user {} (admin:{})".format(
        current_user.id if not current_user.is_anonymous() else None,
        current_user.is_admin if not current_user.is_anonymous else False
    ))
    if current_user.is_anonymous():
        if raise_exception:
            abort(401)
        else:
            return None


def save_data_spreadsheet(name, folder=None):
    if folder is None:
        folder = current_app.config['UPLOAD_FOLDER']
    spreadsheet_file = name
    user_dir = upload_dir_user(folder)
    if not spreadsheet_file.startswith(user_dir):
        spreadsheet_file = helpers.safe_join(user_dir, name + '.xlsx')


def delete_spreadsheet(name, user_id=None):
    spreadsheet_file = name
    for parent_dir in [TEMPLATEDIR, current_app.config['UPLOAD_FOLDER']]:
        user_dir = upload_dir_user(parent_dir, user_id)
        if not spreadsheet_file.startswith(user_dir):
            spreadsheet_file = helpers.safe_join(user_dir, name + '.xlsx')
        if os.path.exists(spreadsheet_file):
            os.remove(spreadsheet_file)


def load_parset_list(project):
    parsets = []

    for parset in project.parsets.values():

        parsets.append({
            "id": parset.uid,
            "project_id": project.uid,
            "pars": parset.pars,
            "updated": parset.modified,
            "created": parset.created,
            "name": parset.name
        })

    return parsets


def get_project_parameters(project):
    return parse_parameters_of_parset_list(project.parsets.values())


def get_parset_from_project(project, parset_id):
    if not isinstance(parset_id, UUID):
        parset_id = UUID(parset_id)
    for parset in project.parsets.values():
        if parset.uid == parset_id:
            return parset
    raise ParsetDoesNotExist(project_id=project.uid, id=parset_id)


def get_optimization_from_project(project, optim_id):
    if not isinstance(optim_id, UUID):
        optim_id = UUID(optim_id)

    optims = [
        project.optims[key]
        for key in project.optims
        if project.optims[key].uid == optim_id
    ]
    if not optims:
        raise ValueError("Optimisation does not exist", project_id=project.uid, id=optim_id)
    return optims[0]


def load_result_record(project_id, parset_id, calculation_type=ResultsDb.DEFAULT_CALCULATION_TYPE):
    result_record = db.session.query(ResultsDb).filter_by(
        project_id=project_id, parset_id=parset_id, calculation_type=calculation_type).first()
    if result_record is None:
        return None
    return result_record


def load_result(project_id, parset_id, calculation_type=ResultsDb.DEFAULT_CALCULATION_TYPE):
    result_record = load_result_record(project_id, parset_id, calculation_type)
    if result_record is None:
        return None
    return result_record.load()


def load_result_by_id(result_id):
    result_record = db.session.query(ResultsDb).get(result_id)
    if result_record is None:
        return None
    return result_record.load()


def update_or_create_result_record(
        project,
        result,
        parset_name='default',
        calculation_type=ResultsDb.DEFAULT_CALCULATION_TYPE,
        db_session=None):

    if db_session is None:
        db_session = db.session

    result_record = db_session.query(ResultsDb).get(result.uid)
    if result_record is not None:
        print ">>> Updating record for result '%s' of parset '%s' from '%s'" % (result.name, parset_name, calculation_type)
    else:
        parset = project.parsets[parset_name]
        result_record = ResultsDb(
            parset_id=parset.uid,
            project_id=project.uid,
            calculation_type=calculation_type)
        print ">>> Creating record for result '%s' of parset '%s' from '%s'" % (result.name, parset_name, calculation_type)

    result_record.id = result.uid
    result_record.save_obj(result)
    db_session.add(result_record)
    db_session.commit()

    return result_record


def delete_result(
        project_id, parset_id, calculation_type, db_session=None):
    if db_session is None:
        db_session = db.session
    records = db_session.query(ResultsDb).filter_by(
        project_id=project_id,
        parset_id=parset_id,
        calculation_type=calculation_type
    )
    records.delete()
    db_session.commit()


def delete_optimization_result(
        project_id, result_name, db_session=None):
    if db_session is None:
        db_session = db.session

    print ">>> Deleting outdated result '%s' of an optimization" % result_name

    records = db_session.query(ResultsDb).filter_by(
        project_id=project_id,
        calculation_type="optimization"
    )
    for record in records:
        result = record.load()
        if result.name == result_name:
            db_session.delete(record)
    db_session.commit()


def save_result(
        project_id, result, parset_name='default',
        calculation_type=ResultsDb.DEFAULT_CALCULATION_TYPE,
        db_session=None):
    if db_session is None:
        db_session = db.session
    project = load_project(project_id)
    result_record = update_or_create_result_record(
        project, result, parset_name=parset_name,
        calculation_type=calculation_type, db_session=db_session)
    db_session.add(result_record)
    db_session.flush()
    db_session.commit()


def load_result_by_optimization(project, optimization):

    result_name = "optim-" + optimization.name
    parset_id = project.parsets[optimization.parsetname].uid

    result_records = db.session.query(ResultsDb).filter_by(
        project_id=project.uid,
        parset_id=parset_id,
        calculation_type="optimization")

    for result_record in result_records:
        result = result_record.load()
        print ">>> Matching optim result '%s' == '%s'" % (result.name, result_name)
        if result.name == result_name:
            return result

    return None


def get_project_years(project):
    settings = project.settings
    return range(int(settings.start), int(settings.end) + 1)


def get_target_popsizes(project, parset, progset, program):

    years = get_project_years(project)
    popsizes = program.gettargetpopsize(t=years, parset=parset)
    return normalize_obj(dict(zip(years, popsizes)))


def load_parameters_from_progset_parset(project, progset, parset):

    print ">>> Fetching target parameters from progset '%s'", progset.name
    progset.gettargetpops()
    progset.gettargetpars()
    progset.gettargetpartypes()

    settings = project.settings

    return parse_parameters_from_progset_parset(settings, progset, parset)


########################################################################
#
# Scenario functions
#
# Data structure of a JSON scenario summary
#
# scenario_summary:
#     id: uuid_string
#     progset_id: uuid_string -or- null # since parameter scenarios don't have progsets
#     parset_id: uuid_string
#     name: string
#     active: boolean
#     years: list of number
#     scenario_type: "parameter", "coverage" or "budget"
#     ---
#     pars:
#     	- name: string
#     	  for: string -or- [1 string] -or- [2 strings]
#     	  startyear: number
#     	  endyear: number
#     	  startval: number
#     	  endval: number
#     	- ...
#      -or-
#     budget:
#     	- program: string
#     	  values: [number -or- null] # same length as years
#     	- ...
#      -or-
#     coverage:
#     	- program: string
#     	  values: [number -or- null] # same length as years
#     	- ...



def get_parameters_for_scenarios(project):
    """
    Returns parameters that can be modified in a scenario:
        <parsetID>:
            <parameterShort>:
                - val: number
                - label: string
    """
    parsets = {key: value for key, value in project.parsets.items()}
    y_keys = {
        str(parset.uid): {
            par.short: [
                {
                    'val': k,
                    'label': ' - '.join(k) if isinstance(k, tuple) else k
                }
                for k in par.y.keys()
            ]
            for par in parset.pars[0].values()
            if hasattr(par, 'y') and par.visible
        }
        for id, parset in parsets.iteritems()
    }
    return y_keys


def get_scenario_summary(project, scenario):
    """
    Returns scenario_summary as defined above
    """
    extra_data = {}

    # budget, coverage, parameter, any others?
    if isinstance(scenario, op.Parscen):
        scenario_type = "parameter"
        extra_data["pars"] = revert_pars_list(scenario.pars)
    elif isinstance(scenario, op.Coveragescen):
        scenario_type = "coverage"
        extra_data["coverage"] = scenario.coverage
    elif isinstance(scenario, op.Budgetscen):
        scenario_type = "budget"
        extra_data["budget"] = [{"program": x, "values": y} for x, y in scenario.budget.iteritems()]

    if hasattr(scenario, "progsetname"):
        progset_id = project.progsets[scenario.progsetname].uid
    else:
        progset_id = None

    if hasattr(scenario, "uid"):
        scenario_id = scenario.uid
    elif hasattr(scenario, "uuid"):
        scenario_id = scenario.uuid
    else:
        scenario_id = op.uuid()

    result = {
        'id': scenario_id,
        'progset_id': progset_id, # could be None if parameter scenario
        'scenario_type': scenario_type,
        'active': scenario.active,
        'name': scenario.name,
        'years': scenario.t,
        'parset_id': project.parsets[scenario.parsetname].uid,
    }
    result.update(extra_data)
    return result


def get_scenario_summaries(project):

    scenario_summaries = map(partial(get_scenario_summary, project), project.scens.values())
    return normalize_obj(scenario_summaries)


def save_scenario_summaries(project, scenario_summaries):
    # delete any records with id's that aren't in summaries

    project.scens = op.odict()

    for s in scenario_summaries:

        if s["parset_id"]:
            parset_name = get_parset_from_project(project, s["parset_id"]).name
        else:
            parset_name = False

        kwargs = {
            "name": s["name"],
            "active": s["active"],
            "parsetname": parset_name,
            "t": s.get("years"),

        }

        if "progset_id" in s and s["progset_id"]:
            progset_name = get_progset_from_project(project, s["progset_id"]).name

        if s["scenario_type"] == "parameter":
            scen = op.Parscen(
                pars=convert_pars_list(s["pars"]),
                **kwargs)

        elif s["scenario_type"] == "coverage":
            scen = op.Coveragescen(
                coverage=s["coverage"],
                progsetname=progset_name,
                **kwargs)
        elif s["scenario_type"] == "budget":
            budget = op.odict({x["program"]:x["values"] for x in s["budget"]})

            scen = op.Budgetscen(
                budget=budget,
                progsetname=progset_name,
                **kwargs)

        if s.get("id"):
            scen.uid = UUID(s["id"])

        project.scens[scen.name] = scen


def make_scenarios_graphs(project_id):
    db.session\
        .query(ResultsDb)\
        .filter_by(project_id=project_id, calculation_type="scenarios")\
        .delete()
    db.session.commit()
    project = load_project(project_id)
    project.runscenarios()
    result = project.results[-1]
    record = update_or_create_result_record(
        project, result, 'default', 'scenarios')
    db.session.add(record)
    db.session.commit()
    return make_mpld3_graph_dict(result)


## PROGRAMS

def load_project_record(project_id, raise_exception=False, db_session=None, authenticate=True):
    if not db_session:
        db_session = db.session

    if authenticate:
        authenticate_current_user()

    if authenticate is False or current_user.is_admin:
        query = db_session.query(ProjectDb).filter_by(id=project_id)
    else:
        query = db_session.query(ProjectDb).filter_by(
            id=project_id, user_id=current_user.id)

    project_record = query.first()

    if project_record is None:
        current_app.logger.warning("no such project found: %s for user %s %s" % (project_id, cu.id, cu.name))
        if raise_exception:
            raise ProjectDoesNotExist(id=project_id)

    return project_record


def load_project(project_id, raise_exception=True, db_session=None, authenticate=True):
    if not db_session:
        db_session = db.session
    project_record = load_project_record(
        project_id, raise_exception=raise_exception,
        db_session=db_session, authenticate=authenticate)
    if project_record is None:
        if raise_exception:
            raise ProjectDoesNotExist(id=project_id)
        else:
            return None
    return project_record.load()



def get_program_from_progset(progset, program_id, include_inactive=False):

    if not isinstance(program_id, UUID):
        program_id = UUID(program_id)

    if include_inactive:
        progset_programs = {}
        progset_programs.update(progset.programs)
        progset_programs.update(progset.inactive_programs)
    else:
        progset_programs = progset.programs

    programs = [
        progset_programs[key]
        for key in progset_programs
        if progset_programs[key].uid == program_id
    ]
    if not programs:
        raise ProgramDoesNotExist(id=program_id)
    return programs[0]



def get_progset_from_project(project, progset_id):
    if not isinstance(progset_id, UUID):
        progset_id = UUID(progset_id)

    progsets = [
        project.progsets[key]
        for key in project.progsets
        if project.progsets[key].uid == progset_id
    ]
    if not progsets:
        raise ProgsetDoesNotExist(project_id=project.uid, id=progset_id)
    return progsets[0]


def load_project_program_summaries(project_id):
    project = load_project(project_id, raise_exception=True)
    return parse_default_program_summaries(project)


def get_progset_summary(project, progset_name):
    """

    @TODO: targetpartypes and readytooptimize fields needs to be made consistent within ProgsetDb

    """

    progset = project.progsets[progset_name]

    active_programs = map(partial(parse_program_summary, progset=progset, active=True), progset.programs.values()),
    inactive_programs_odict = getattr(progset, "inactive_programs", {})
    inactive_programs = map(partial(parse_program_summary, progset=progset, active=False), inactive_programs_odict.values()),
    programs = list(active_programs[0]) + list(inactive_programs[0])

    default_programs = parse_default_program_summaries(project)

    # Overwrite with default name and category if applicable
    loaded_program_shorts = []
    default_program_by_short = {p['short']: p for p in default_programs}
    for program in programs:
        short = program['short']
        if short in default_program_by_short:
            default_program = default_program_by_short[short]
            if not program['name']:
                program['name'] = default_program['name']
            program['category'] = default_program['category']
        loaded_program_shorts.append(short)

    # append any default programs as inactive if not already in project
    for program in default_programs:
        if program['short'] not in loaded_program_shorts:
            programs.append(program)

    for program in programs:
        if program['category'] == 'No category':
            program['category'] = 'Other'

    progset_summary = {
        'id': progset.uid,
        'name': progset.name,
        'created': progset.created,
        'updated': progset.modified,
        'programs': programs,
        #'targetpartypes': progset_record.targetpartypes,
        #'readytooptimize': progset_record.readytooptimize
    }
    return progset_summary


def get_progset_summaries(project):
    progset_summaries = [
        get_progset_summary(project, name) for name in project.progsets]
    return {'progsets': normalize_obj(progset_summaries)}


def save_program_summary(progset, summary):

    try:
        program = get_program_from_progset(progset, summary["id"], include_inactive=True)

        # It exists, so remove it first...
        try:
            progset.programs.pop(program.short)
        except KeyError:
            progset.inactive_programs.pop(program.short)

        program_id = program.uid
    except ProgramDoesNotExist:
        program_id = None
        pass

    program = op.Program(
        short=summary["short"],
        name=summary["name"],
        category=summary["category"],
        targetpars=revert_targetpars(summary["targetpars"]),
        targetpops=summary["populations"],
        criteria=summary["criteria"],
        ccopars=revert_ccopars(summary["ccopars"]),
        costcovdata=revert_costcovdata(summary["costcov"]))

    if program_id:
        program.uid = program_id

    if summary["active"]:
        progset.addprograms(program)
    else:
        progset.inactive_programs[program.short] = program

    progset.updateprogset()


def save_progset_summaries(project, progset_summaries, progset_id=None):
    """

    """
    progset_name = progset_summaries['name']
    progset_programs = progset_summaries['programs']

    if progset_name not in project.progsets:
        if progset_id:
            # It may have changed, so try getting via ID if we have it...
            progset = get_progset_from_project(project, progset_id)
            project.progsets.pop(progset.name)

            # Update the name and its reflection in the project.
            progset.name = progset_name
            project.progsets[progset_name] = progset
        else:
            # Probably a new one.
            project.progsets[progset_name] = op.Programset(name=progset_name)
    progset = project.progsets[progset_name]

    # Clear the current programs...
    progset.programs = op.odict()
    progset.inactive_programs = op.odict()

    for p in progset_programs:
        save_program_summary(progset, p)

    progset.updateprogset()

    current_app.logger.debug("!!! name and programs data : %s, \n\t %s "%(progset_name, progset_programs))


################

def get_optimization_summaries(project):

    optimizations = []

    for o in project.optims.values():

        optim = {
            "id": o.uid,
            "name": o.name,
            "objectives": o.objectives,
            "constraints": o.constraints,
        }

        optim["which"] = o.objectives["which"]

        if o.parsetname:
            optim["parset_id"] = project.parsets[o.parsetname].uid
        else:
            optim["parset_id"] = None

        if o.progsetname:
            optim["progset_id"] = project.progsets[o.progsetname].uid
        else:
            optim["progset_id"] = None

        optimizations.append(optim)

    return optimizations


def save_optimization_summaries(project, optimization_summaries):
    """
    The optimization summary is generated by the web-client and by the parsing
    algorithm for project.optims objects.

    Args:
        project_id: uuid_string
        optimization_summaries: a list of optimizations where each optimization is:

            {'constraints': {'max': {'ART': None,
                                     'Condoms': None,
                                     'FSW programs': None,
                                     'HTC': None,
                                     'Other': 1},
                             'min': {'ART': 1,
                                     'Condoms': 0,
                                     'FSW programs': 0,
                                     'HTC': 0,
                                     'Other': 1},
                             'name': {'ART': 'Antiretroviral therapy',
                                      'Condoms': 'Condom promotion and distribution',
                                      'FSW programs': 'Programs for female sex workers and clients',
                                      'HTC': 'HIV testing and counseling',
                                      'Other': 'Other'}},
             'name': 'Optimization 1',
             'objectives': {'base': None,
                            'budget': 60500000,
                            'deathfrac': None,
                            'deathweight': 5,
                            'end': 2030,
                            'incifrac': None,
                            'inciweight': 1,
                            'keylabels': {'death': 'Deaths', 'inci': 'New infections'},
                            'keys': ['death', 'inci'],
                            'start': 2017,
                            'which': 'outcomes'},
             'parset_id': 'af6847d6-466b-4fc7-9e41-1347c053a0c2',
             'progset_id': 'cfa49dcc-2b8b-11e6-8a08-57d606501764',
             'which': 'outcomes'}
    """
    new_optims = op.odict()

    for summary in optimization_summaries:
        id = summary.get('id', None)

        if id is None:
            optim = op.Optim(project=project)
        else:
            optim = get_optimization_from_project(project, id)

        optim.name = summary["name"]
        optim.parsetname = get_parset_from_project(project, summary["parset_id"]).name
        optim.progsetname = get_progset_from_project(project, summary["progset_id"]).name
        optim.objectives = summary["objectives"]
        optim.objectives["which"] = summary["which"]
        if "constraints" in summary:
            optim.constraints = summary["constraints"]

        new_optims[summary["name"]] = optim

    project.optims = new_optims


def get_default_optimization_summaries(project):
    defaults_by_progset_id = {}
    for progset in project.progsets.values():
        progset_id = progset.uid
        default = {
            'constraints': op.defaultconstraints(project=project, progset=progset),
            'objectives': {}
        }
        for which in ['outcomes', 'money']:
            default['objectives'][which] = op.defaultobjectives(
                project=project, progset=progset, which=which)
        defaults_by_progset_id[progset_id] = default

    return normalize_obj(defaults_by_progset_id)


def get_populations_from_project(project):
    data_pops = normalize_obj(project.data.get("pops"))
    populations = []
    for i in range(len(data_pops['short'])):
        population = {
            'short': data_pops['short'][i],
            'name': data_pops['long'][i],
            'male': bool(data_pops['male'][i]),
            'female': bool(data_pops['female'][i]),
            'age_from': int(data_pops['age'][i][0]),
            'age_to': int(data_pops['age'][i][1]),
            'injects': bool(data_pops['injects'][i]),
            'sexworker': bool(data_pops['sexworker'][i]),
        }
        populations.append(population)
    return populations


def set_populations_on_project(project, populations):
    """
    <odist>
     - short: ['FSW', 'Clients', 'MSM', 'PWID', 'M 15+', 'F 15+']
     - long: ['Female sex workers', 'Clients of sex workers', 'Men who have sex with men', 'People who inject drugs', 'Males 15+', 'Females 15+']
     - male: [0, 1, 1, 1, 1, 0]
     - female: [1, 0, 0, 0, 0, 1]
     - age: [[15, 49], [15, 49], [15, 49], [15, 49], [15, 49], [15, 49]]
     - injects: [0, 0, 0, 1, 0, 0]
     - sexworker: [1, 0, 0, 0, 0, 0]
    """
    data_pops = op.odict()

    for key in ['short', 'long', 'male', 'female', 'age', 'injects', 'sexworker']:
        data_pops[key] = []

    for pop in populations:
        data_pops['short'].append(pop['short'])
        data_pops['long'].append(pop['name'])
        data_pops['male'].append(int(pop['male']))
        data_pops['female'].append(int(pop['female']))
        data_pops['age'].append((int(pop['age_from']), int(pop['age_to'])))
        data_pops['injects'].append(int(pop['injects']))
        data_pops['sexworker'].append(int(pop['sexworker']))

    if project.data.get("pops") != data_pops:
        # We need to delete the data here off the project?
        project.data = {}

    project.data["pops"] = data_pops

    project.data["npops"] = len(populations)


def set_project_summary_on_project(project, summary):

    set_populations_on_project(project, summary.get('populations', {}))
    project.name = summary["name"]

    if not project.settings:
        project.settings = op.Settings()

    project.settings.start = summary["dataStart"]
    project.settings.end = summary["dataEnd"]


def get_project_summary_from_project_record(project_record):
    try:
        project = project_record.load()
    except:
        return {
            'id': project_record.id,
            'name': "Failed loading"
        }

    years = project.data.get('years')
    if years:
        data_start = years[0]
        data_end = years[-1]
    else:
        data_start = project.settings.start
        data_end = project.settings.end

    n_program = 0
    for progsets in project.progsets.values():
        this_n_program = len(progsets.programs.values())
        if this_n_program > n_program:
            n_program = this_n_program

    result = {
        'id': project_record.id,
        'name': project.name,
        'userId': project_record.user_id,
        'dataStart': data_start,
        'dataEnd': data_end,
        'populations': get_populations_from_project(project),
        'nProgram': n_program,
        'creationTime': project.created,
        'updatedTime': project.modified,
        'dataUploadTime': project.spreadsheetdate,
        'hasData': project.data != {},
        'hasEcon': "econ" in project.data
    }
    return result


def save_project_with_new_uids(project, user_id):
    project_record = ProjectDb(user_id)
    db.session.add(project_record)
    db.session.flush()

    project.uid = project_record.id

    # TODO: these need to double-checked for consistency
    for parset in project.parsets.values():
        parset.uid = op.uuid()
    for result in project.results.values():
        result.uid = op.uuid()

    project_record.save_obj(project)
    db.session.flush()

    db.session.commit()
