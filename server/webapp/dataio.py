from server.webapp.parse import parse_parameters_of_parset_list, parse_parameters_from_progset_parset

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

from flask import helpers, current_app, abort
from flask.ext.login import current_user

from server.webapp.dbconn import db
from server.webapp.dbmodels import ProjectDb, ResultsDb, ParsetsDb, ProgsetsDb, ProgramsDb, WorkingProjectDb
from server.webapp.exceptions import (
    ProjectDoesNotExist, ProgsetDoesNotExist, ParsetDoesNotExist, ProgramDoesNotExist)
from server.webapp.utils import TEMPLATEDIR, upload_dir_user, OptimaJSONEncoder, normalize_obj
from server.webapp.parse import parse_default_program_summaries

import optima as op
from optima.utils import saves


def load_project_record(project_id, all_data=False, raise_exception=False, db_session=None):
    from sqlalchemy.orm import defaultload
    from server.webapp.exceptions import ProjectDoesNotExist
    if not db_session:
        db_session = db.session
    cu = current_user
    current_app.logger.debug("getting project {} for user {} (admin:{})".format(
        project_id,
        cu.id if not cu.is_anonymous() else None,
        cu.is_admin if not cu.is_anonymous else False
    ))
    if cu.is_anonymous():
        if raise_exception:
            abort(401)
        else:
            return None
    if cu.is_admin:
        query = db_session.query(ProjectDb).filter_by(id=project_id)
    else:
        query = db_session.query(ProjectDb).filter_by(id=project_id, user_id=cu.id)
    if all_data:
        query = query.options(
            # undefer('model'),
            # defaultload(ProjectDb.working_project).undefer('model'),
            defaultload(ProjectDb.project_data).undefer('meta'))
    project_record = query.first()
    if project_record is None:
        current_app.logger.warning("no such project found: %s for user %s %s" % (project_id, cu.id, cu.name))
        if raise_exception:
            raise ProjectDoesNotExist(id=project_id)
    return project_record


def _load_project_child(
        project_id, record_id, record_class, exception_class, raise_exception=True):
    cu = current_user

    print ">>> Fetching record_id", record_id, "of", repr(record_class)
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

    return record


def load_progset_record(project_id, progset_id, raise_exception=True):
    return _load_project_child(
        project_id, progset_id, ProgsetsDb, ProgsetDoesNotExist, raise_exception)


def load_parset_record(project_id, parset_id, raise_exception=True):
    return _load_project_child(
        project_id, parset_id, ParsetsDb, ParsetDoesNotExist, raise_exception)


def load_program_record(project_id, progset_id, program_id, raise_exception=True):
    cu = current_user
    current_app.logger.debug("getting project {} for user {}".format(progset_id, cu.id))

    progset_record = load_progset_record(
        project_id, progset_id, raise_exception=raise_exception)

    program_record = db.session.query(ProgramsDb).get(program_id)

    if program_record.progset_id != progset_record.id:
        if raise_exception:
            raise ProgramDoesNotExist(id=program_id)
        return None

    return program_record


def load_scenario_record(project_id, scenario_id, raise_exception=True):
    from server.webapp.dbmodels import ScenariosDb
    from server.webapp.exceptions import ScenarioDoesNotExist

    cu = current_user
    current_app.logger.debug("getting scenario {} for user {}".format(scenario_id, cu.id))

    scenario_record = db.session.query(ScenariosDb).get(scenario_id)

    if scenario_record is None:
        if raise_exception:
            raise ScenarioDoesNotExist(id=scenario_id)
        return None

    if scenario_record.project_id != project_id:
        if raise_exception:
            raise ScenarioDoesNotExist(id=scenario_id)
        return None

    return scenario_record


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


def update_or_create_parset_record(project_id, name, parset):
    parset_record = ParsetsDb.query.filter_by(id=parset.uid, project_id=project_id).first()
    if parset_record is None:
        parset_record = ParsetsDb(
            id=parset.uid,
            project_id=project_id,
            name=name,
            created=parset.created or datetime.now(dateutil.tz.tzutc()),
            updated=parset.modified or datetime.now(dateutil.tz.tzutc()),
            pars=saves(parset.pars)
        )

        db.session.add(parset_record)
    else:
        parset_record.updated = datetime.now(dateutil.tz.tzutc())
        parset_record.name = name
        parset_record.pars = saves(parset.pars)
        db.session.add(parset_record)


def update_or_create_progset_record(project_id, name, progset):
    progset_record = ProgsetsDb.query \
        .filter_by(project_id=project_id, name=name) \
        .first()

    if progset_record is None:
        progset_record = ProgsetsDb(
            project_id=project_id,
            name=name,
            created=progset.created or datetime.now(dateutil.tz.tzutc()),
            updated=datetime.now(dateutil.tz.tzutc())
        )
        db.session.add(progset_record)
        db.session.flush()
    else:
        progset_record.updated = datetime.now(dateutil.tz.tzutc())
        db.session.add(progset_record)

    return progset_record


def update_or_create_program_record(project_id, progset_id, short, program_summary):
    program_record = ProgramsDb.query\
        .filter_by(short=short, project_id=project_id, progset_id=progset_id)\
        .first()
    if program_record is None:
        program_record = ProgramsDb(
            project_id=project_id,
            progset_id=progset_id,
            short=short,
            name=program_summary.get('name', ''),
            created=datetime.now(dateutil.tz.tzutc()),
        )
    program_record.update_from_summary(program_summary)
    db.session.add(program_record)
    return program_record


def update_or_create_scenario_record(project_id, project, name):  # project might have a different ID than the one we want

    from server.webapp.dbmodels import ScenariosDb, ParsetsDb, ProgsetsDb
    import json

    parset_id = None
    progset_id = None
    blob = {}
    scenario_type = None

    scenario = project.scens[name]
    if not scenario:
        raise Exception("scenario {} not present in project {}!".format(name, project_id))

    if isinstance(scenario, op.Parscen):
        scenario_type = 'parameter'
    elif isinstance(scenario, op.Budgetscen):
        scenario_type = 'budget'
    elif isinstance(scenario, op.Coveragescen):
        scenario_type = 'coverage'

    if scenario.t:
        blob['years'] = scenario.t
    for key in ['budget', 'coverage', 'pars']:
        if hasattr(scenario, key) and getattr(scenario, key):
            val = getattr(scenario, key)
            blob[key] = json.loads(json.dumps(val, cls=OptimaJSONEncoder))

    parset_name = scenario.parsetname
    if parset_name:
        parset_record = ParsetsDb.query \
            .filter_by(project_id=project_id, name=parset_name) \
            .first()
        if parset_record:
            parset_id = parset_record.id

    progset_id = None
    if hasattr(scenario, 'progsetname') and scenario.progsetname:
        progset_name = scenario.progsetname
        progset_record = ProgsetsDb.query \
            .filter_by(project_id=project_id, name=progset_name) \
            .first()
        if progset_record:
            progset_id = progset_record.id

    scenario_record = ScenariosDb.query \
        .filter_by(project_id=project_id, name=name) \
        .first()

    if scenario_record is None:
        scenario_record = ScenariosDb(
            project_id=project_id,
            parset_id=parset_id,
            progset_id=progset_id,
            name=name,
            scenario_type=scenario_type,
            active=scenario.active,
            blob=blob
        )
        db.session.add(scenario_record)
        db.session.flush()
    else:
        scenario_record.parset_id = parset_id
        scenario_record.scenario_type = scenario_type
        scenario_record.active=scenario.active
        scenario_record.blob = blob
        db.session.add(scenario_record)

    return scenario_record


def update_or_create_optimization_record(project_id, project, name):

    from server.webapp.dbmodels import OptimizationsDb, ProgsetsDb, ParsetsDb

    parset_id = None
    progset_id = None

    optim = project.optims[name]
    if not optim:
        raise Exception("optimization {} not present in project {}!".format(name, project_id))

    parset_name = optim.parsetname
    if parset_name:
        parset_record = ParsetsDb.query \
        .filter_by(project_id=project_id, name=parset_name) \
        .first()
        if parset_record:
            parset_id = parset_record.id

    progset_name = optim.progsetname
    if progset_name:
        progset_record = ProgsetsDb.query \
        .filter_by(project_id=project_id, name=progset_name) \
        .first()
        if progset_record:
            progset_id = progset_record.id

    optimization_record = OptimizationsDb.query.filter_by(name=name, project_id=project_id).first()
    if optimization_record is None:
        optimization_record = OptimizationsDb(
            project_id=project_id,
            name=name,
            which = optim.objectives.get('which', 'outcome') if optim.objectives else 'outcome',
            parset_id=parset_id,
            progset_id=progset_id,
            objectives=(optim.objectives or {}),
            constraints=(optim.constraints or {})
        )
        db.session.add(optimization_record)
        db.session.flush()
    else:
        optimization_record.which = optim.objectives.get('which', 'outcome') if optim.objectives else 'outcome'
        optimization_record.parset_id = parset_id
        optimization_record.progset_id = progset_id
        optimization_record.objectives = (optim.objectives or {})
        optimization_record.constraints = (optim.constraints or {})
        db.session.add(optimization_record)

    return optimization_record


def load_project(project_id, autofit=False, raise_exception=True):
    if not autofit:
        project_record = load_project_record(project_id, raise_exception=raise_exception)
        if project_record is None:
            raise ProjectDoesNotExist(id=project_id)
        project = project_record.hydrate()
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
    return program_entry.hydrate()


def load_parset(project_id, parset_id):
    from server.webapp.dbmodels import ParsetsDb
    from server.webapp.exceptions import ParsetDoesNotExist

    parset_record = db.session.query(ParsetsDb).get(parset_id)
    if parset_record is None:
        if raise_exception:
            raise ParsetDoesNotExist(id=parset_id)
        return None

    if parset_record.project_id != project_id:
        if raise_exception:
            raise ParsetDoesNotExist(id=parset_id)
        return None

    return parset_record.hydrate()


def load_parset_list(project_id):
    parset_records = db.session.query(ParsetsDb).filter_by(project_id=project_id).all()
    return [parset_record.hydrate() for parset_record in parset_records]


def get_project_parameters(project_id):
    return parse_parameters_of_parset_list(load_parset_list(project_id))


def get_parset_from_project(project, parset_id):
    parsets = [
        project.parsets[key]
        for key in project.parsets
        if project.parsets[key].uid == parset_id
    ]
    if not parsets:
        raise ParsetDoesNotExist(project_id=project_id, id=parset_id)
    return parsets[0]


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
        project_id, result, parset_name='default',
        calculation_type=ResultsDb.CALIBRATION_TYPE,
        db_session=None):

    if not db_session:
        db_session=db.session

    # find relevant parset for the result
    print("save_result(%s, %s, %s" % (project_id, parset_name, calculation_type))
    parsets = db_session.query(ParsetsDb).filter_by(project_id=project_id)
    parset = [item for item in parsets if item.name == parset_name]
    if parset:
        parset = parset[0]
    else:
        raise Exception("parset '{}' not generated for the project {}!".format(parset_name, project_id))

    # update results (after runsim is invoked)
    result_records = db_session.query(ResultsDb).filter_by(project_id=project_id)
    result_record = [item for item in result_records
                     if item.parset_id == parset.id
                        and item.calculation_type == calculation_type]
    if result_record:
        if len(result_record) > 1:
            abort(500, "Found multiple records for result")
        result_record = result_record[0]
        result_record.blob = op.saves(result)

    if not result_record:
        result_record = ResultsDb(
            parset_id=parset.id,
            project_id=project_id,
            calculation_type=calculation_type,
            blob=op.saves(result)
        )

    return result_record


def load_project_program_summaries(project_id):
    return parse_default_program_summaries(load_project(project_id, raise_exception=True))


def get_project_years(project_id):
    settings = load_project(project_id).settings
    return range(int(settings.start), int(settings.end) + 1)


def get_target_popsizes(project_id, parset_id, progset_id, program_id):
    program = load_program(project_id, progset_id, program_id)
    parset = load_parset(project_id, parset_id)
    years = get_project_years(project_id)
    popsizes = program.gettargetpopsize(t=years, parset=parset)
    return normalize_obj(dict(zip(years, popsizes)))


def load_parameters_from_progset_parset(project_id, progset_id, parset_id):
    progset_record = load_progset_record(project_id, progset_id)
    progset = progset_record.hydrate()
    print ">>> Fetching target parameters from progset", progset_id
    progset.gettargetpops()
    progset.gettargetpars()
    progset.gettargetpartypes()

    parset_record = load_parset_record(project_id, parset_id)
    parset = parset_record.hydrate()

    settings = load_project(project_id).settings

    return parse_parameters_from_progset_parset(settings, progset, parset)
