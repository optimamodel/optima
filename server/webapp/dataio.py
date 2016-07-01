from flask.ext.restful import marshal

__doc__ = """

dataio.py contains all the functions that fetch and saves optima objects to/from database
and the file system. These functions abstracts out the data i/o for the web-server
api calls.

function call pairs are load_*/save_* and refers to saving to database.

Database record variables should have suffix _record

Parsed data structures should have suffix _summary
"""


import os
from datetime import datetime
import dateutil
from pprint import pprint
from functools import partial
from uuid import UUID

from flask import helpers, current_app, abort
from flask.ext.login import current_user

from server.webapp.dbconn import db
from server.webapp.dbmodels import ProjectDb, ResultsDb
from server.webapp.exceptions import (
    ProjectDoesNotExist, ProgsetDoesNotExist, ParsetDoesNotExist, ProgramDoesNotExist)
from server.webapp.utils import TEMPLATEDIR, upload_dir_user, normalize_obj
from server.webapp.parse import (
    parse_default_program_summaries, parse_parameters_of_parset_list,
    parse_parameters_from_progset_parset, revert_targetpars, parse_program_summary,
    revert_costcovdata, parse_outcomes_from_progset, revert_ccopars, put_outcomes_into_progset,
)


import optima as op
from optima.utils import saves

def load_project_record(project_id, all_data=False, raise_exception=False, db_session=None, authenticate=True):
    from sqlalchemy.orm import defaultload
    from server.webapp.exceptions import ProjectDoesNotExist


    if not db_session:
        db_session = db.session

    if authenticate:
        cu = current_user
        # current_app.logger.debug("getting project {} for user {} (admin:{})".format(
        #     project_id,
        #     cu.id if not cu.is_anonymous() else None,
        #     cu.is_admin if not cu.is_anonymous else False
        # ))
        if cu.is_anonymous():
            if raise_exception:
                abort(401)
            else:
                return None
    if authenticate is False or cu.is_admin:
        query = db_session.query(ProjectDb).filter_by(id=project_id)
    else:
        query = db_session.query(ProjectDb).filter_by(id=project_id, user_id=cu.id)

    project_record = query.first()
    if project_record is None:
        current_app.logger.warning("no such project found: %s for user %s %s" % (project_id, cu.id, cu.name))
        if raise_exception:
            raise ProjectDoesNotExist(id=project_id)
    return project_record


def check_project_exists(project_id):
    project_record = load_project_record(project_id)
    if project_record is None:
        raise ProjectDoesNotExist(id=project_id)


def _load_project_child(
        project_id, record_id, record_class, exception_class, raise_exception=True):
    cu = current_user

    record = db.session.query(record_class).get(record_id)
    if record is None:
        if raise_exception:
            raise exception_class(id=record_id)
        return None

    if record.project_id != project_id:
        if raise_exception:
            raise exception_class(id=record_id)
        return None

    if not cu.is_admin and record.project.user_id != cu.id:
        if raise_exception:
            raise exception_class(id=record_id)
        return None

    print ">>> Fetching record '%s' of '%s'" % (record.name, repr(record_class))

    return record

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


def load_project(project_id, autofit=False, raise_exception=True):
    if not autofit:
        project_record = load_project_record(project_id, raise_exception=raise_exception)
        if project_record is None:
            raise ProjectDoesNotExist(id=project_id)
        project = project_record.load()
    else:  # todo bail out if no working project
        working_project_record = db.session.query(WorkingProjectDb).filter_by(id=project_id).first()
        if working_project_record is None:
            raise ProjectDoesNotExist(id=project_id)
        project = op.loads(working_project_record.project)
    return project


def load_program(project_id, progset_id, program_id):
    program_entry = load_program_record(project_id, progset_id, program_id)
    if program_entry is None:
        raise ProgramDoesNotExist(id=program_id, project_id=project_id)
    return program_entry.load()


def load_parset(project, parset_id):

    for parset in project.parsets.values():
        if parset.uid == parset_id:
            return parset



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

    parsets = [
        project.parsets[key]
        for key in project.parsets
        if project.parsets[key].uid == parset_id
    ]
    if not parsets:
        raise ParsetDoesNotExist(project_id=project.uid, id=parset_id)
    return parsets[0]


def get_progset_from_project(project, progset_id):
    if not isinstance(progset_id, UUID):
        print(progset_id)
        progset_id = UUID(progset_id)

    progsets = [
        project.progsets[key]
        for key in project.progsets
        if project.progsets[key].uid == progset_id
    ]
    if not progsets:
        raise ProgsetDoesNotExist(project_id=project.uid, id=progset_id)
    return progsets[0]



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



def load_result_record(project_id, parset_id, calculation_type=ResultsDb.CALIBRATION_TYPE):
    result_record = db.session.query(ResultsDb).filter_by(
        project_id=project_id, parset_id=parset_id, calculation_type=calculation_type).first()
    if result_record is None:
        return None
    return result_record


def load_result(project_id, parset_id, calculation_type=ResultsDb.CALIBRATION_TYPE):
    result_record = load_result_record(project_id, parset_id, calculation_type)
    if result_record is None:
        return None
    return result_record.hydrate()



def save_result(
        project, result, parset_name='default',
        calculation_type=ResultsDb.CALIBRATION_TYPE,
        db_session=None):

    if not db_session:
        db_session=db.session

    # find relevant parset for the result
    print ">>>> Saving result(%s) '%s' of parset '%s'" % (calculation_type, result.name, parset_name)
    parsets = project.parsets.values()
    parset = [item for item in parsets if item.name == parset_name]
    if parset:
        parset = parset[0]
    else:
        raise Exception("parset '{}' not generated for the project {}!".format(parset_name, project_id))

    # update results (after runsim is invoked)
    result_records_from_db = db_session.query(ResultsDb).filter_by(project_id=project.uid)
    result_records = [item for item in result_records_from_db
                     if item.parset_id == parset.uid
                        and item.calculation_type == calculation_type]

    blob = op.saves(result)
    if result_records:
        if len(result_records) > 1:
            abort(500, "Found multiple records for result (%s) of parset '%s'" % calculation_type, parset.name)
        result_record = result_records[0]
        result_record.blob = blob
        print "> Updating results", result.uid

    if not result_records:
        result_record = ResultsDb(
            parset_id=str(parset.uid),
            project_id=project.uid,
            calculation_type=calculation_type,
            blob=blob)
        print "> Creating results", result.uid

    result_id = str(result.uid)
    result_record.id = result_id

    return result_record


def load_project_program_summaries(project_id):
    return parse_default_program_summaries(load_project(project_id, raise_exception=True))


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


def get_parset_keys_with_y_values(project):

    y_keys = {
        id: {
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
        for id, parset in project.parsets.iteritems()
        }
    return y_keys


def get_scenario_summary(project, scenario):
    """

    Args:
        scenario_record:

    Returns:
    {
        'id': scenario_record.id,
        'progset_id': scenario_record.progset_id,
        'scenario_type': scenario_record.scenario_type,
        'active': scenario_record.active,
        'name': scenario_record.name,
        'parset_id': scenario_record.parset_id,
        'budgets': [
          {
            "program": "VMMC",
            "values": [ null ]
          },
          },
          {
            "program": "HTC",
            "values": [ 33333 ]
          },
          "years": [ 2020 ],
    }
    """
    extra_data = {}

    # budget, coverage, parameter, any others?
    if isinstance(scenario, op.Parscen):
        scenario_type = "parameter"
        extra_data["pars"] = scenario.pars
    elif isinstance(scenario, op.Coveragescen):
        scenario_type = "coverage"
        extra_data["coverage"] = scenario.coverage
    elif isinstance(scenario, op.Budgetscen):
        scenario_type = "budget"
        extra_data["budget"] = scenario.budget

    if hasattr(scenario, "progsetname"):
        progset_id = project.progsets[scenario.progsetname].uid
    else:
        progset_id = None

    result = {
        'id': scenario.uid,
        'progset_id': progset_id, # could be None if parameter scenario
        'scenario_type': scenario_type,
        'active': scenario.active,
        'name': scenario.name,
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

        print(s)

        if s["parset_id"]:
            parset_name = get_parset_from_project(project, s["parset_id"]).name
        else:
            parset_name = False

        kwargs = {
            "name": s["name"],
            "active": s["active"],
            "parsetname": parset_name,

        }

        if "progset_id" in s and s["progset_id"]:
            progset_name = get_progset_from_project(project, s["progset_id"]).name

        if s["scenario_type"] == "parameter":
            par = op.Parscen(
                pars=s["pars"],
                **kwargs)

        elif s["scenario_type"] == "coverage":
            par = op.Coveragescen(
                coverage=s["coverage"],
                progsetname=progset_name,
                **kwargs)
        elif s["scenario_type"] == "budget":
            par = op.Budgetscen(
                budget=s["budget"],
                progsetname=progset_name,
                **kwargs)

        if s.get("id"):
            par.uid = UUID(s["id"])

        project.scens[par.name] = par




def get_progset_summary(progset):
    """

    @TODO: targetpartypes and readytooptimize fields needs to be made consistent within ProgsetDb

    """

    active_programs = map(partial(parse_program_summary, progset=progset, active=True), progset.programs.values()),

    inactive_programs_list = getattr(progset, "inactive_programs", {})
    inactive_programs = map(partial(parse_program_summary, progset=progset, active=False), inactive_programs_list.values()),


    progset_summary = {
        'id': progset.uid,
        'name': progset.name,
        'created': progset.created,
        'updated': progset.modified,
        'programs': list(active_programs[0]) + list(inactive_programs[0]),
        #'targetpartypes': progset_record.targetpartypes,
        #'readytooptimize': progset_record.readytooptimize
    }
    return progset_summary

def get_progset_summaries(project):
    """

    """
    progset_summaries = map(get_progset_summary, project.progsets.values())
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




def get_optimization_summaries(project_id):
    optimization_records = db.session.query(OptimizationsDb) \
        .filter_by(project_id=project_id).all()
    result = marshal(optimization_records, OptimizationsDb.resource_fields)
    return normalize_obj(result)


def save_optimization_summaries(project_id, optimization_summaries):
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

    existing_ids = [
        summary['id']
        for summary in optimization_summaries
        if summary.get('id', False)
    ]

    db.session.query(OptimizationsDb) \
        .filter_by(project_id=project_id) \
        .filter(~OptimizationsDb.id.in_(existing_ids)) \
        .delete(synchronize_session='fetch')
    db.session.flush()

    for summary in optimization_summaries:
        id = summary.get('id', None)

        if id is None:
            record = OptimizationsDb(
                project_id=project_id,
                parset_id=summary['parset_id'],
                progset_id=summary['progset_id'],
                name=summary['name'],
                which=summary['which'])
        else:
            record = db.session.query(OptimizationsDb).get(id)

        record.update(
            constraints=summary['constraints'],
            objectives=summary['objectives'])

        # verb = "Creating" if id is None else "Updating"
        # print ">>>", verb, " optimizaton", summary['name']
        # pprint(summary)

        db.session.add(record)
        db.session.flush()

    db.session.commit()


def get_default_optimization_summaries(project_id):
    project = load_project(project_id)
    progset_records = ProgsetsDb.query.filter_by(project_id=project_id).all()

    defaults_by_progset_id = {}
    for progset_record in progset_records:
        progset = progset_record.hydrate()
        progset_id = progset_record.id
        default = {
            'constraints': op.defaultconstraints(project=project, progset=progset),
            'objectives': {}
        }
        for which in ['outcomes', 'money']:
            default['objectives'][which] = op.defaultobjectives(
                project=project, progset=progset, which=which)
        defaults_by_progset_id[progset_id] = default

    return normalize_obj(defaults_by_progset_id)
