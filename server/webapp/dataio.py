"""

dataio.py
=========

Contains all the functions that fetches and saves optima objects to/from database
and the file system. These functions abstracts out the data i/o for the web-server
api calls.

Function call pairs are load_*/save_* and refers to saving to database.

Database record variables should have suffix _record

Parsed data structures should have suffix _summary

All parameters and return types are either id's, json-summaries, or mpld3 graphs
"""
import traceback
from functools import wraps
import os
from zipfile import ZipFile
from uuid import uuid4, UUID
from datetime import datetime
import dateutil

from flask import current_app, abort, request, session, make_response, jsonify
from flask_login import current_user, login_user, logout_user
from werkzeug.utils import secure_filename
from validate_email import validate_email

import optima as op

from .dbconn import db
from . import parse
from .exceptions import ProjectDoesNotExist, ParsetAlreadyExists, \
    UserAlreadyExists, UserDoesNotExist, InvalidCredentials
from .dbmodels import UserDb, ProjectDb, ResultsDb, PyObjectDb
from .plot import make_mpld3_graph_dict, convert_to_mpld3


TEMPLATEDIR = "/tmp"  # CK: hotfix to prevent ownership issues


def templatepath(filename):
    """
    "Normalizes" filename:  if it is full path, leaves it alone. Otherwise, prepends it with datadir.
    """

    datadir = TEMPLATEDIR
    if datadir == None:
        datadir = current_app.config['UPLOAD_FOLDER']

    result = filename

    # get user dir path
    datadir = upload_dir_user(datadir)

    if not (os.path.exists(datadir)):
        os.makedirs(datadir)
    if os.path.dirname(filename) == '' and not os.path.exists(filename):
        result = os.path.join(datadir, filename)

    return result


#############################################################################################
### USERS
#############################################################################################

def upload_dir_user(dirpath, user_id=None):
    """
    Returns a unique directory on the server for the user's files
    """
    try:
        from flask.ext.login import current_user

        # get current user
        if current_user.is_anonymous() == False:

            current_user_id = user_id if user_id else current_user.id

            # user_path
            user_path = os.path.join(dirpath, str(current_user_id))

            # if dir does not exist
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)

            # if dir with user id does not exist
            if not os.path.exists(user_path):
                os.makedirs(user_path)

            return user_path
    except:
        return dirpath

    return dirpath


def authenticate_current_user(raise_exception=True):
    current_app.logger.debug("authenticating user {} (admin:{})".format(
        current_user.id if not current_user.is_anonymous() else None,
        current_user.is_admin if not current_user.is_anonymous else False
    ))
    if current_user.is_anonymous():
        if raise_exception:
            abort(401)
        else:
            return None


def parse_user_record(user_record):
    return {
        'id': user_record.id,
        'displayName': user_record.name,
        'username': user_record.username,
        'email': user_record.email,
        'is_admin': user_record.is_admin,
    }


def get_user_summaries():
    return {'users': [parse_user_record(q) for q in UserDb.query.all()]}


def nullable_email(email_str):
    if not email_str:
        return email_str
    if validate_email(email_str):
        return email_str
    raise ValueError('{} is not a valid email'.format(email_str))


def hashed_password(password_str):
    if isinstance(password_str, basestring) and len(password_str) == 56:
        return password_str
    raise ValueError(
        'Invalid password - expecting SHA224 - Received {} of length {} and type {}'.format(
            password_str, len(password_str), type(password_str)))


def parse_user_args(args):
    return {
        'email': nullable_email(args.get('email', None)),
        'name': args.get('displayName', ''),
        'username': args.get('username', ''),
        'password': hashed_password(args.get('password')),
    }


def create_user(args):
    """
    Creates a user and returns a user summary.
    """
    n_user = UserDb.query.filter_by(username=args['username']).count()
    if n_user > 0:
        raise UserAlreadyExists(args['username'])

    user = UserDb(**args)
    db.session.add(user)
    db.session.commit()

    return parse_user_record(user)


def update_user(user_id, args):
    """
    Updates user by args and returns a user summary
    """
    user = UserDb.query.get(user_id)
    if user is None:
        raise UserDoesNotExist(user_id)

    try:
        userisanonymous = current_user.is_anonymous()  # CK: WARNING, SUPER HACKY way of dealing with different Flask versions
    except:
        userisanonymous = current_user.is_anonymous

    if userisanonymous or (str(user_id) != str(current_user.id) and not current_user.is_admin):
        secret = request.args.get('secret', '')
        u = UserDb.query.filter_by(password=secret, is_admin=True).first()
        if u is None:
            abort(403)

    for key, value in args.iteritems():
        if value is not None:
            setattr(user, key, value)

    db.session.commit()

    return parse_user_record(user)


def do_login_user(args):
    try:
        userisanonymous = current_user.is_anonymous()  # CK: WARNING, SUPER HACKY way of dealing with different Flask versions
    except:
        userisanonymous = current_user.is_anonymous

    if userisanonymous:
        current_app.logger.debug("current user anonymous, proceed with logging in")

        print(">> do_login_user args", args)
        try:
            # Get user for this username
            user = UserDb.query.filter_by(username=args['username']).first()

            print(">> do_login_user user", user)
            # Make sure user is valid and password matches
            if user is not None and user.password == args['password']:
                login_user(user)
                return parse_user_record(user)

        except Exception:
            var = traceback.format_exc()
            print("do_login_user error logging user {}: \n{}".format(args['username'], var))

        raise InvalidCredentials

    else:
        return parse_user_record(current_user)


def delete_user(user_id):
    user = UserDb.query.get(user_id)

    if user is None:
        raise UserDoesNotExist(user_id)

    user_email = user.email
    user_name = user.username
    from server.webapp.dbmodels import ProjectDb
    from sqlalchemy.orm import load_only

    # delete all corresponding projects and working projects as well
    # project and related records delete should be on a method on the project model
    projects = ProjectDb.query.filter_by(user_id=user_id).options(load_only("id")).all()
    for project in projects:
        project.recursive_delete()

    db.session.delete(user)
    db.session.commit()

    print(">> delete_user user:{} {} {}".format(user_id, user_name, user_email))


def do_logout_current_user():
    logout_user()
    session.clear()


def report_exception_decorator(api_call):
    @wraps(api_call)
    def _report_exception(*args, **kwargs):
        from werkzeug.exceptions import HTTPException
        try:
            return api_call(*args, **kwargs)
        except Exception as e:
            exception = traceback.format_exc()
            # limiting the exception information to 10000 characters maximum
            # (to prevent monstrous sqlalchemy outputs)
            current_app.logger.error("Exception during request %s: %.10000s" % (request, exception))
            if isinstance(e, HTTPException):
                raise
            code = 500
            reply = {'exception': exception}
            return make_response(jsonify(reply), code)

    return _report_exception


def verify_admin_request_decorator(api_call):
    """
    verification by secret (hashed pw) or by being a user with admin rights
    """

    @wraps(api_call)
    def _verify_admin_request(*args, **kwargs):
        u = None
        if (not current_user.is_anonymous()) and current_user.is_authenticated() and current_user.is_admin:
            u = current_user
        else:
            secret = request.args.get('secret', '')
            u = UserDb.query.filter_by(password=secret, is_admin=True).first()
        if u is None:
            abort(403)
        else:
            current_app.logger.debug("admin_user: %s %s %s" % (u.name, u.password, u.email))
            return api_call(*args, **kwargs)

    return _verify_admin_request




#############################################################################################
### PROJECT
#############################################################################################

def load_project_record(project_id, raise_exception=True, db_session=None, authenticate=False):
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
        if raise_exception:
            raise ProjectDoesNotExist(id=project_id)

    return project_record


def save_project(project, db_session=None, is_skip_result=False):
    if not db_session:
        db_session = db.session
    project_record = load_project_record(project.uid, db_session=db_session)
    new_project = op.dcp(project)
    # Copy the project, only save what we want...
    new_project.spreadsheet = None
    if is_skip_result:
        new_project.results = op.odict()
    project_record.save_obj(new_project)
    db_session.add(project_record)
    db_session.commit()


def load_project_from_record(project_record):
    project = project_record.load()
    project.restorelinks()
    if resolve_project(project):
        save_project(project)
    for progset in project.progsets.values():
        if not hasattr(progset, 'inactive_programs'):
            progset.inactive_programs = op.odict()
    return project


def load_project(project_id, raise_exception=True, db_session=None, authenticate=True):
    if not db_session:
        db_session = db.session
    project_record = load_project_record(
        project_id,
        raise_exception=raise_exception,
        db_session=db_session,
        authenticate=authenticate)
    if project_record is None:
        if raise_exception:
            raise ProjectDoesNotExist(id=project_id)
        else:
            return None
    return load_project_from_record(project_record)


def update_project_with_fn(project_id, update_project_fn, db_session=None):
    if db_session is None:
        db_session = db.session
    project = load_project(project_id, db_session=db_session)
    update_project_fn(project)
    project.modified = datetime.now(dateutil.tz.tzutc())
    save_project(project, db_session=db_session)


def load_project_summary_from_project_record(project_record):
    project = load_project_from_record(project_record)
    project_summary = parse.get_project_summary_from_project(project)
    project_summary['userId'] = project_record.user_id
    return project_summary


def load_project_summary(project_id):
    project_entry = load_project_record(project_id)
    return load_project_summary_from_project_record(project_entry)


def load_current_user_project_summaries():
    query = ProjectDb.query.filter_by(user_id=current_user.id)
    return {'projects': map(load_project_summary_from_project_record, query.all())}


def load_all_project_summaries():
    query = ProjectDb.query
    return {'projects': map(load_project_summary_from_project_record, query.all())}


def get_default_populations():
    return {'populations': parse.get_default_populations()}


def create_project_with_spreadsheet_download(user_id, project_summary):
    """
    Creates a project from project_summary and returns
    - project_id
    - directory_of_template_spreadsheet
    - template_spreadsheet_filename)
    """
    project_entry = ProjectDb(user_id=user_id)
    db.session.add(project_entry)
    db.session.flush()

    project = op.Project(name=project_summary["name"])
    project.created = datetime.now(dateutil.tz.tzutc())
    project.modified = datetime.now(dateutil.tz.tzutc())
    project.uid = project_entry.id

    data_pops = parse.revert_populations_to_pop(project_summary["populations"])
    project.data["pops"] = data_pops
    project.data["npops"] = len(data_pops)

    save_project(project)

    new_project_template = secure_filename(
        "{}.xlsx".format(project_summary['name']))
    path = templatepath(new_project_template)
    op.makespreadsheet(
        path,
        pops=project_summary['populations'],
        datastart=project_summary['startYear'],
        dataend=project_summary['endYear'])

    print("> create_project_with_spreadsheet_download %s" % new_project_template)

    return project.uid, upload_dir_user(TEMPLATEDIR), new_project_template


def create_project(user_id, project_summary):
    """
    Creates a project from project_summary and returns
    - project_id
    - directory_of_template_spreadsheet
    - template_spreadsheet_filename)
    """
    project_entry = ProjectDb(user_id=user_id)
    db.session.add(project_entry)
    db.session.flush()

    project = op.Project(name=project_summary["name"])
    project.created = datetime.now(dateutil.tz.tzutc())
    project.modified = datetime.now(dateutil.tz.tzutc())
    project.uid = project_entry.id

    data_pops = parse.revert_populations_to_pop(project_summary["populations"])
    project.data["pops"] = data_pops
    project.data["npops"] = len(data_pops)

    save_project(project)

    return {'projectId': str(project.uid)}


def download_template(project_summary):
    new_project_template = secure_filename(
        "{}.xlsx".format(project_summary['name']))
    path = templatepath(new_project_template)
    op.makespreadsheet(
        path,
        pops=project_summary['populations'],
        datastart=project_summary['startYear'],
        dataend=project_summary['endYear'])

    print("> create_project_with_spreadsheet_download %s" % new_project_template)

    return path


def delete_projects(project_ids):
    for project_id in project_ids:
        record = load_project_record(project_id, raise_exception=True)
        record.recursive_delete()
    db.session.commit()


def update_project_from_summary(project_summary, is_delete_data=False):
    project = load_project(project_summary['id'])
    if is_delete_data:
        parse.clear_project_data(project)
    parse.set_project_summary_on_project(project, project_summary)
    save_project(project)


def download_data_spreadsheet(project_id, is_blank=True):
    print ">> download_data_spreadsheet init"
    project = load_project(project_id)
    project_summary = parse.get_project_summary_from_project(project)
    new_project_template = secure_filename(
        "{}.xlsx".format(project_summary['name']))
    path = templatepath(new_project_template)
    if is_blank:
        op.makespreadsheet(
            path,
            pops=project_summary['populations'],
            datastart=project_summary["startYear"],
            dataend=project_summary["endYear"])
    else:
        op.makespreadsheet(path, data=project.data)
    return path


def save_project_as_new(project, user_id):
    project_record = ProjectDb(user_id)
    db.session.add(project_record)
    db.session.flush()

    project.uid = project_record.id

    for attr in ['parsets','progsets','scens','optims','results']:
        for obj in getattr(project,attr).values():
            obj.uid = op.uuid()

    print(">> save_project_as_new '%s'" % project.name)
    for result in project.results.values():
        name = result.name
        if 'scenarios' in name:
            update_or_create_result_record_by_id(
                result, project.uid, None, 'scenarios')
        if 'optim' in name:
            update_or_create_result_record_by_id(
                result, project.uid, None, 'optimization')
        if 'parset' in name:
            update_or_create_result_record_by_id(
                result, project.uid, result.parset.uid, 'calibration')
    db.session.commit()

    project.created = datetime.now(dateutil.tz.tzutc())
    project.modified = datetime.now(dateutil.tz.tzutc())

    save_project(project)


def copy_project(project_id, new_project_name):
    """
    Returns the project_id of the copied project
    """
    project_record = load_project_record(
        project_id, raise_exception=True)
    user_id = project_record.user_id
    project = load_project_from_record(project_record)
    project.name = new_project_name
    save_project_as_new(project, user_id)

    parset_name_by_id = {parset.uid: name for name, parset in project.parsets.items()}
    copy_project_id = project.uid

    # copy each result
    result_records = project_record.results
    if result_records:
        for result_record in result_records:
            # reset the parset_id in results to new project
            result = result_record.load()
            parset_id = result_record.parset_id
            if parset_id not in parset_name_by_id:
                continue
            parset_name = parset_name_by_id[parset_id]
            new_parset = [r for r in project.parsets.values() if r.name == parset_name]
            if not new_parset:
                continue
            copy_parset_id = new_parset[0].uid

            copy_result_record = ResultsDb(
                copy_parset_id, copy_project_id, result_record.calculation_type)
            db.session.add(copy_result_record)
            db.session.flush()

            # serializes result with new
            result.uid = copy_result_record.id
            copy_result_record.save_obj(result)

    db.session.commit()

    return { 'projectId': copy_project_id }


def get_unique_name(name, other_names=None):
    if other_names is None:
        other_names = [p['name'] for p in load_current_user_project_summaries()]
    i = 0
    unique_name = name
    while unique_name in other_names:
        i += 1
        unique_name = "%s (%d)" % (name, i)
    return unique_name


def create_project_from_prj_file(prj_filename, user_id, other_names):
    """
    Returns the project id of the new project.
    """
    print(">> create_project_from_prj_file '%s'" % prj_filename)
    project = op.loadproj(prj_filename)
    project.name = get_unique_name(project.name, other_names)
    save_project_as_new(project, user_id)
    return { 'projectId': str(project.uid) }


def create_project_from_spreadsheet(xlsx_filename, user_id, other_names):
    """
    Returns the project id of the new project.
    """
    print(">> create_project_from_spreadsheet '%s'" % xlsx_filename)
    project = op.Project(spreadsheet=xlsx_filename)
    project.name = get_unique_name(project.name, other_names)
    save_project_as_new(project, user_id)
    return { 'projectId': str(project.uid) }


def download_project(project_id):
    """
    Returns the (dirname, filename) of the .prj binary of the project on the server
    """
    project = load_project(project_id, raise_exception=True)
    dirname = upload_dir_user(TEMPLATEDIR)
    if not dirname:
        dirname = TEMPLATEDIR
    server_filename = project.save(folder=dirname, saveresults=False)
    print(">> download_project %s" % (server_filename))
    return server_filename


def download_project_with_result(project_id):
    """
    Returns the filenae of the .prj binary of the project on the server
    """
    project = load_project(project_id, raise_exception=True)
    result_records = db.session.query(ResultsDb).filter_by(project_id=project_id)
    if result_records is not None:
        for result_record in result_records:
            result = result_record.load()
            print(">> download_project_with_result result '%s'" % result.name)
            project.addresult(result)
    dirname = upload_dir_user(TEMPLATEDIR)
    if not dirname:
        dirname = TEMPLATEDIR
    server_filename = project.save(folder=dirname, saveresults=True)
    print(">> download_project_with_result %s" % (server_filename))
    return server_filename


def update_project_from_uploaded_spreadsheet(spreadsheet_fname, project_id):
    def modify(project):
        project.loadspreadsheet(spreadsheet_fname, name='default', overwrite=True, makedefaults=True)
    update_project_with_fn(project_id, modify)


def load_zip_of_prj_files(project_ids):
    """
    Returns the (dirname, filename) of the .zip of the selected projects on the server
    """
    dirname = upload_dir_user(TEMPLATEDIR)
    if not dirname:
        dirname = TEMPLATEDIR

    prjs = [load_project_record(id).as_file(dirname) for id in project_ids]

    zip_fname = '{}.zip'.format(uuid4())
    server_zip_fname = os.path.join(dirname, zip_fname)
    with ZipFile(server_zip_fname, 'w') as zipfile:
        for prj in prjs:
            zipfile.write(os.path.join(dirname, prj), 'portfolio/{}'.format(prj))

    return dirname, zip_fname


def resolve_project(project):
    """
    Returns boolean to whether any changes needed to be made to the project.
    Checks project to ensure that all the cross-reference fields are
    properly specified and that defaults are sensibly populated.
    """
    is_change = False
    print(">> resolve_project '%s'" % project.name)

    # Handle scenarios
    del_scenario_keys = []
    for scenario_key, scenario in project.scens.items():
        if type(scenario.parsetname) is int:
            i = scenario.parsetname
            try:
                scenario.parsetname = project.parsets[i].name
                is_change = True
            except:
                del_scenario_keys.append(scenario_key)
        elif scenario.parsetname not in project.parsets:
            del_scenario_keys.append(scenario_key)
        if hasattr(scenario, "progsetname"):
            if type(scenario.progsetname) is int:
                i = scenario.progsetname
                try:
                    scenario.progsetname = project.progsets[i].name
                    is_change = True
                except:
                    del_scenario_keys.append(scenario_key)
            if scenario.progsetname not in project.progsets:
                del_scenario_keys.append(scenario_key)
    if del_scenario_keys:
        for scenario_key in del_scenario_keys:
            print(">> resolve_project delete %s" % scenario_key)
            project.scens.pop(scenario_key, None)

    is_change = is_change or len(del_scenario_keys) > 0

    # check optimizations are good
    del_optim_keys = []
    for optim_key, optim in project.optims.items():
        if type(optim.parsetname) is int:
            i = optim.parsetname
            try:
                optim.parsetname = project.parsets[i].name
                is_change = True
            except:
                del_optim_keys.append(optim_key)
        elif optim.parsetname not in project.parsets:
            del_optim_keys.append(optim_key)
        if hasattr(optim, "progsetname"):
            if type(optim.progsetname) is int:
                i = optim.progsetname
                try:
                    optim.progsetname = project.progsets[i].name
                    is_change = True
                except:
                    del_optim_keys.append(optim_key)
            if optim.progsetname not in project.progsets:
                del_optim_keys.append(optim_key)
    if del_optim_keys:
        for optim_key in del_optim_keys:
            print(">> resolve_project delete optim %s" % optim_key)
            project.optims.pop(optim_key, None)

    is_change = is_change or len(del_optim_keys) > 0

    # ensure constraints set to None are given a default
    for optim in project.optims.values():
        progset_name = optim.progsetname
        progset = project.progsets[progset_name]
        if optim.constraints is None:
            optim.constraints = op.defaultconstraints(project=project, progset=progset)
            is_change = True

    results = db.session.query(ResultsDb).filter_by(project_id=project.uid)
    parset_ids = [parset.uid for parset in project.parsets.values()]
    is_delete_result = False
    for result in results:
        if result.parset_id is not None and result.parset_id not in parset_ids:
            print(">> resolve_project delete result %s" % result.parset_id)
            db.session.delete(result)
            is_delete_result = True
    db.session.commit()

    is_change = is_change or is_delete_result

    return is_change


def get_server_filename(basename):
    dirname = upload_dir_user(TEMPLATEDIR)
    if not dirname:
        dirname = TEMPLATEDIR
    return os.path.join(dirname, basename)


def download_project_object(project_id, obj_type, obj_id):
    """
    Args:
        project_id: id of project
        obj_type: "parset", "progset", "scenario", "optimization" 
        obj_id: id of object

    Returns: 
        server filename
    """
    project = load_project(project_id)
    if obj_type == "parset":
        ext = "par"
        obj = parse.get_parset_from_project(project, obj_id)
    elif obj_type == "progset":
        ext = "prg"
        obj = parse.get_progset_from_project(project, obj_id)
    elif obj_type == "scenario":
        ext = "scn"
        obj = parse.get_scenario_from_project(project, obj_id)
    elif obj_type == "optimization":
        ext = "opt"
        obj = parse.get_optimization_from_project(project, obj_id)

    basename = "%s-%s.%s" % (project.name, obj.name, ext)
    filename = get_server_filename(basename)
    op.saveobj(filename, obj)
    return filename


def upload_project_object(filename, project_id, obj_type):
    """
    Args:
        project_id: id of project
        obj_type: "parset", "progset", "scenario", "optimization" 
        obj_id: id of object

    Returns: 
        server filename
    """
    project = load_project(project_id)
    obj = op.loadobj(filename)
    obj.uid = op.uuid()
    if obj_type == "parset":
        project.addparset(parset=obj, overwrite=True)
    elif obj_type == "progset":
        project.addprogset(progset=obj, overwrite=True)
    elif obj_type == "scenario":
        project.addscen(scen=obj, overwrite=True)
    elif obj_type == "optimization":
        project.addoptim(optim=obj, overwrite=True)
    save_project(project)
    return { 'name': obj.name }



#############################################################################################
### RESULTS
#############################################################################################

def load_result(
        project_id, parset_id, calculation_type=ResultsDb.DEFAULT_CALCULATION_TYPE,
        which=None, name=None):
    kwargs = {
        'calculation_type': calculation_type
    }
    if parset_id is not None:
        kwargs['parset_id'] = parset_id
    if project_id is not None:
        kwargs['project_id'] = project_id
    print(">> load_result name", name, "kwargs", kwargs)
    result_records = db.session.query(ResultsDb).filter_by(**kwargs)
    if result_records.count() == 0:
        print(">> load_result: none")
        return None
    if name:
        for result_record in result_records:
            result = result_record.load()
            if result.name == name:
                break
        else:
            result = None
    else:
        result_record = result_records.first()
        result = result_record.load()
    if result:
        print(">> load_result %s" % str(result.name))
        if which:
            result.which = which
            print(">> load_result saving which", which)
            result_record.save_obj(result)
    else:
        print(">> load_result: none")
        db.session.delete(result_record)
    return result


def load_result_by_id(result_id, which=None):
    result_record = db.session.query(ResultsDb).get(result_id)
    if result_record is None:
        raise Exception("Results '%s' does not exist" % result_id)
    result = result_record.load()
    if which is not None:
        result.which = which
        print(">> load_result_by_id saving which", which)
        result_record.save_obj(result)
    return result


def update_or_create_result_record_by_id(
        result,
        project_id,
        parset_id,
        calculation_type=ResultsDb.DEFAULT_CALCULATION_TYPE,
        db_session=None):

    if db_session is None:
        db_session = db.session

    result_record = db_session.query(ResultsDb).get(result.uid)
    if result_record is not None:
        print(">> update_or_create_result_record_by_id update %s" % (result.name))
    else:
        result_record = ResultsDb(
            parset_id=parset_id,
            project_id=project_id,
            calculation_type=calculation_type)
        print(">> update_or_create_result_record_by_id create %s" % (result.name))

    result_record.id = result.uid
    result_record.save_obj(result)
    db_session.add(result_record)

    return result_record


def delete_result_by_parset_id(
        project_id, parset_id, calculation_type=None, db_session=None):
    if db_session is None:
        db_session = db.session
    if calculation_type is None:
        records = db_session.query(ResultsDb).filter_by(
            project_id=project_id, parset_id=parset_id)
    else:
        records = db_session.query(ResultsDb).filter_by(
            project_id=project_id, parset_id=parset_id,
            calculation_type=calculation_type)
    for record in records:
        record.cleanup()
    records.delete()
    db_session.commit()


def delete_result_by_name(
        project_id, result_name, db_session=None):
    if db_session is None:
        db_session = db.session

    records = db_session.query(ResultsDb).filter_by(project_id=project_id)
    for record in records:
        result = record.load()
        if result.name == result_name:
            print(">> delete_result_by_name '%s'" % result_name)
            record.cleanup()
            db_session.delete(record)
    db_session.commit()


def download_result_data(result_id):
    """
    Returns (dirname, basename) of the the result.csv on the server -- WARNING, deprecated function name!
    """
    dirname = upload_dir_user(TEMPLATEDIR)
    if not dirname:
        dirname = TEMPLATEDIR
    result = load_result_by_id(result_id)
    return result.export(folder=dirname)


def load_result_by_optimization(project, optimization):

    result_name = "optim-" + optimization.name
    parset_id = project.parsets[optimization.parsetname].uid

    print(">> load_result_by_optimization '%s'" % result_name)
    result_records = db.session.query(ResultsDb).filter_by(
        project_id=project.uid,
        parset_id=parset_id,
        calculation_type="optimization")

    for result_record in result_records:
        result = result_record.load()
        if result.name == result_name:
            return result

    print(">> load_result_by_optimization not result for optim '%s'" % (optimization.name))

    return None


def load_result_mpld3_graphs(result_id=None, which=None, zoom=None, startYear=None, endYear=None):
    result = load_result_by_id(result_id, which)
    return make_mpld3_graph_dict(result=result, which=which, zoom=zoom, startYear=startYear, endYear=endYear)


def download_figures(result_id=None, which=None, filetype=None, index=None):
    result = load_result_by_id(result_id, which)
    dirname = upload_dir_user(TEMPLATEDIR)
    if not dirname:
        dirname = TEMPLATEDIR
    
    filenames = op.saveplots(result, toplot=which, folder=dirname, filename=None, filetype=filetype, index=index)
    if len(filenames)>1:
        errormsg = 'Webapp only supports saving one figure at a time; you are trying to save %s' % len(filenames)
        raise op.OptimaException(errormsg)
    else:
        server_filename = filenames[0]
    print(">> download_figures", server_filename)
    return server_filename


#############################################################################################
### PARSETS
#############################################################################################

def copy_parset(project_id, parset_id, new_parset_name):

    def update_project_fn(project):
        original_parset = parse.get_parset_from_project(project, parset_id)
        original_parset_name = original_parset.name
        project.copyparset(orig=original_parset_name, new=new_parset_name)
        project.parsets[new_parset_name].uid = op.uuid()

    update_project_with_fn(project_id, update_project_fn)

    return load_parset_summaries(project_id)


def delete_parset(project_id, parset_id):

    def update_project_fn(project):
        parset = parse.get_parset_from_project(project, parset_id)
        project.parsets.pop(parset.name)

    update_project_with_fn(project_id, update_project_fn)
    delete_result_by_parset_id(project_id, parset_id)


def rename_parset(project_id, parset_id, new_parset_name):

    def update_project_fn(project):
        parset = parse.get_parset_from_project(project, parset_id)
        old_parset_name = parset.name
        parset.name = new_parset_name
        del project.parsets[old_parset_name]
        project.parsets[new_parset_name] = parset

    update_project_with_fn(project_id, update_project_fn)


def create_parset(project_id, new_parset_name):

    def update_project_fn(project):
        if new_parset_name in project.parsets:
            raise ParsetAlreadyExists(project_id, new_parset_name)
        project.makeparset(new_parset_name, overwrite=False)

    update_project_with_fn(project_id, update_project_fn)

    return load_parset_summaries(project_id)


def refresh_parset(project_id, parset_id):

    def update_project_fn(project):
        parset = parse.get_parset_from_project(project, parset_id)
        parset_name = parset.name
        project.refreshparset(name=parset_name)

    update_project_with_fn(project_id, update_project_fn)
    delete_result_by_parset_id(project_id, parset_id)


def load_parset_summaries(project_id):
    project = load_project(project_id)
    return {"parsets": parse.get_parset_summaries(project)}


def load_project_parameters(project_id):
    return {'parameters': parse.get_parameters_for_edit_program(load_project(project_id)) }


def load_parameters_from_progset_parset(project_id, progset_id, parset_id):
    project = load_project(project_id)
    return parse.get_parameters_for_outcomes(project, progset_id, parset_id)


def load_parameters(project_id, parset_id):
    project = load_project(project_id)
    parset = parse.get_parset_from_project(project, parset_id)
    return parse.get_parameters_from_parset(parset)


def save_parameters(project_id, parset_id, parameters):

    def update_project_fn(project):
        parset = parse.get_parset_from_project(project, parset_id)
        parset.modified = datetime.now(dateutil.tz.tzutc())
        parse.set_parameters_on_parset(parameters, parset)

    delete_result_by_parset_id(project_id, parset_id)
    update_project_with_fn(project_id, update_project_fn)



def load_parset_graphs(
        project_id, parset_id, calculation_type, which=None,
        parameters=None, zoom=None, startYear=None, endYear=None):

    project = load_project(project_id)
    parset = parse.get_parset_from_project(project, parset_id)

    result = load_result(project_id, parset_id, calculation_type, which)
    if result:
        if not which:
            if hasattr(result, 'which'):
                print(">> load_parset_graphs load stored which of parset '%s'" % parset.name)
                which = result.which

    if parameters is not None:
        print(">> load_parset_graphs updating parset '%s'" % parset.name)
        parset.modified = datetime.now(dateutil.tz.tzutc())
        parse.set_parameters_on_parset(parameters, parset)
        delete_result_by_parset_id(project_id, parset_id)
        save_project(project)
        result = None

    if result is None:
        result = project.runsim(name=parset.name, end=endYear) # When running, possibly modify the end year, but not the start
        result.which = which
        record = update_or_create_result_record_by_id(
            result, project_id, parset_id, calculation_type, db_session=db.session)
        db.session.add(record)
        print(">> load_parset_graphs calc result for parset '%s'" % parset.name)
        db.session.commit()

    graph_dict = make_mpld3_graph_dict(result=result, which=which, zoom=zoom, startYear=startYear, endYear=endYear)

    return {
        "parameters": parse.get_parameters_from_parset(parset),
        "graphs": graph_dict["graphs"]
    }



#############################################################################################
### PROGSETS
#############################################################################################

def load_target_popsizes(project_id, parset_id, progset_id, program_id):
    """
    Returns a dictionary containing
      <year>: float(popsize)
      ...
    """
    project = load_project(project_id)
    parset = parse.get_parset_from_project(project, parset_id)
    progset = parse.get_progset_from_project(project, progset_id)
    program = parse.get_program_from_progset(progset, program_id)
    years = parse.get_project_years(project)
    popsizes = program.gettargetpopsize(t=years, parset=parset)
    return parse.normalize_obj(dict(zip(years, popsizes)))


def load_project_program_summaries(project_id):
    project = load_project(project_id, raise_exception=True)
    return { 'programs': parse.get_default_program_summaries(project) }


def load_progset_summary(project_id, progset_id):
    project = load_project(project_id)
    progset = parse.get_progset_from_project(project, progset_id)
    return parse.get_progset_summary(project, progset.name)


def load_progset_summaries(project_id):
    project = load_project(project_id)
    return parse.get_progset_summaries(project)


def create_progset(project_id, progset_summary):
    """
    Returns progset summary
    """
    project = load_project(project_id)
    parse.set_progset_summary_on_project(project, progset_summary)
    save_project(project)
    return parse.get_progset_summary(project, progset_summary["name"])


def save_progset(project_id, progset_id, progset_summary):
    """
    Returns progset summary
    """
    project = load_project(project_id)
    parse.set_progset_summary_on_project(project, progset_summary, progset_id=progset_id)
    save_project(project)
    return parse.get_progset_summary(project, progset_summary["name"])


def rename_progset(project_id, progset_id, new_name):
    def update_project_fn(project):
        print(">> rename_progset", progset_id, new_name)
        progset = parse.get_progset_from_project(project, progset_id)
        project.renameprogset(orig=progset.name, new=new_name)
    update_project_with_fn(project_id, update_project_fn)


def copy_progset(project_id, progset_id, new_progset_name):

    def update_project_fn(project):
        original_progset = parse.get_progset_from_project(project, progset_id)
        project.copyprogset(orig=original_progset.name, new=new_progset_name)
        project.progsets[new_progset_name].uid = op.uuid()

    update_project_with_fn(project_id, update_project_fn)
    return load_progset_summaries(project_id)


def delete_progset(project_id, progset_id):
    project = load_project(project_id)

    progset = parse.get_progset_from_project(project, progset_id)

    progset_name = progset.name
    optims = [o for o in project.optims.values() if o.progsetname == progset_name]

    for optim in optims:
        result_name = 'optim-' + optim.name
        delete_result_by_name(project.uid, result_name)
        project.optims.pop(optim.name)

    project.progsets.pop(progset.name)

    save_project(project)


def load_progset_outcome_summaries(project_id, progset_id):
    project = load_project(project_id)
    progset = parse.get_progset_from_project(project, progset_id)
    outcomes = parse.get_outcome_summaries_from_progset(progset)
    return outcomes


def save_outcome_summaries(project_id, progset_id, outcome_summaries):
    """
    Returns all outcome summarries
    """
    project = load_project(project_id)
    progset = parse.get_progset_from_project(project, progset_id)
    parse.set_outcome_summaries_on_progset(outcome_summaries, progset)
    save_project(project)
    return parse.get_outcome_summaries_from_progset(progset)


def save_program(project_id, progset_id, program_summary):
    project = load_project(project_id)

    progset = parse.get_progset_from_project(project, progset_id)

    print(">> save_program " + program_summary['name'])
    parse.set_program_summary_on_progset(progset, program_summary)

    progset.updateprogset(verbose=4)

    save_project(project)


def load_costcov_graph(project_id, progset_id, program_id, parset_id, year, zoom=0.5):
    project = load_project(project_id)
    progset = parse.get_progset_from_project(project, progset_id)

    program = parse.get_program_from_progset(progset, program_id)
    plotoptions = None
    if hasattr(program, "attr"):
        plotoptions = program.attr

    parset = parse.get_parset_from_project(project, parset_id)
    plot = op.plotcostcov(program=program, year=year, parset=parset, plotoptions=plotoptions)
    op.reanimateplots(plot)

    graph_dict = convert_to_mpld3(plot, zoom=zoom)

    return graph_dict


def load_reconcile_summary(project_id, progset_id, parset_id, t):

    project = load_project(project_id)
    progset = parse.get_progset_from_project(project, progset_id)
    parset = parse.get_parset_from_project_by_id(project, parset_id)

    budgets = progset.getdefaultbudget()
    if progset.readytooptimize():
        pars = progset.compareoutcomes(parset=parset, year=t)
    else:
        msg = progset.readytooptimize(detail=True)
        pars = [[msg, '', 0, 0]]

    return {
        'budgets': parse.normalize_obj(budgets),
        'pars': parse.normalize_obj(pars),
    }


def launch_reconcile_calc(project_id, progset_id, parset_id, year, maxtime):
    import server.webapp.tasks as tasks
    print(">> launch_reconcile_calc")
    calc_status = tasks.launch_reconcile(project_id, progset_id, parset_id, year, maxtime)
    return calc_status


def any_optimizable(project_id):
    ''' Loop over all progsets and see if any of them are ready to optimize '''
    
    project = load_project(project_id)

    optimizable = False
    for progset in project.progsets.values():
        if progset.readytooptimize():
            optimizable = True
        
    print('>> any_optimizable for %s: %s' % (project.name, optimizable))
    return {'anyOptimizable': optimizable}


#############################################################################################
### SCENARIOS
#############################################################################################


def make_scenarios_graphs(project_id, which=None, is_run=False, zoom=None, startYear=None, endYear=None):
    result = load_result(project_id, None, "scenarios", which)

    if result is None:
        if not is_run:
            print(">> make_scenarios_graphs: no results found")
            return {}
    if not which:
        if hasattr(result, 'which'):
            print(">> make_scenarios_graphs load which")
            which = result.which
    if is_run:
        project = load_project(project_id)
        if len(project.scens) == 0:
            print(">> make_scenarios_graphs no scenarios")
            return {}
        print(">> make_scenarios_graphs project '%s' from %s to %s" % (
            project_id, startYear, endYear))
        # start=None, end=None -> does nothing
        project.runscenarios(end=endYear) # Only change end year from default
        result = project.results[-1]
        if which:
            result.which = which
        record = update_or_create_result_record_by_id(
            result, project.uid, None, 'scenarios')
        db.session.add(record)
        db.session.commit()
    return make_mpld3_graph_dict(result=result, which=which, zoom=zoom, startYear=startYear, endYear=endYear)


def save_scenario_summaries(project_id, scenario_summaries):
    """
    Returns scenario summaries of the projects
    """
    delete_result_by_parset_id(project_id, None, "scenarios")
    project = load_project(project_id)
    parse.set_scenario_summaries_on_project(project, scenario_summaries)
    save_project(project)
    return {'scenarios': parse.get_scenario_summaries(project)}


def load_scenario_summaries(project_id):
    project = load_project(project_id)
    return {
        'scenarios': parse.get_scenario_summaries(project),
        'ykeysByParsetId': parse.get_parameters_for_scenarios(project),
        'defaultBudgetsByProgsetId': parse.get_budgets_for_scenarios(project),
        'defaultCoveragesByParsetIdyProgsetId': parse.get_coverages_for_scenarios(project),
        'years': parse.get_project_years(project)
    }


def load_startval_for_parameter(project_id, parset_id, par_short, pop, year):
    project = load_project(project_id)
    return {'startVal': parse.get_startval_for_parameter(project, parset_id, par_short, pop, year)}



#############################################################################################
### OPTIMIZATIONS
#############################################################################################

def load_optimization_summaries(project_id):
    project = load_project(project_id)
    return {
        'optimizations': parse.get_optimization_summaries(project),
        'defaultOptimizationsByProgsetId': parse.get_default_optimization_summaries(project)
    }


def save_optimization_summaries(project_id, optimization_summaries):
    """
    Returns all optimization summaries
    """
    project = load_project(project_id)
    old_names = [o.name for o in project.optims.values()]
    parse.set_optimization_summaries_on_project(project, optimization_summaries)
    new_names = [o.name for o in project.optims.values()]
    deleted_names = [name for name in old_names if name not in new_names]
    deleted_result_names = ['optim-' + name for name in deleted_names]
    for result_name in deleted_result_names:
        delete_result_by_name(project.uid, result_name)
    save_project(project)
    return {'optimizations': parse.get_optimization_summaries(project)}


def upload_optimization_summary(project_id, optimization_id, optimization_summary):
    """
    Returns all optimization summaries
    """
    project = load_project(project_id)
    old_optim = parse.get_optimization_from_project(project, optimization_id)
    optimization_summary['id'] = optimization_id
    optimization_summary['name'] = old_optim.name
    parse.set_optimization_summaries_on_project(project, [optimization_summary])
    save_project(project)
    return {'optimizations': parse.get_optimization_summaries(project)}


def load_optimization_graphs(project_id=None, optimization_id=None, which=None, zoom=None, startYear=None, endYear=None):
    project = load_project(project_id)
    optimization = parse.get_optimization_from_project(project, optimization_id)
    result_name = optimization.resultsref # Use result name stored in the optimization
    result = load_result(project.uid, None, "optimization", which, result_name)
    if not result:
        return {}
    else:
        if hasattr(result, 'which'):
            which = result.which
        print(">> load_optimization_graphs result '%s' %s" % (result.name, which))
        return make_mpld3_graph_dict(result=result, which=which, zoom=zoom, startYear=startYear, endYear=endYear)




#############################################################################################
### PORTFOLIO
#############################################################################################

def create_portfolio(name, db_session=None, portfolio=None):
    """
    Returns the portfolio summary of the portfolio
    """

    if db_session is None:
        db_session = db.session
    if portfolio is None:
        print("> create_portfolio %s with default objectives" % name)
        portfolio = op.Portfolio()
        portfolio.objectives = op.defaultobjectives()
        portfolio.name = name
    else:
        portfolio.uid = op.uuid() # Have to update this or else the database freaks out
        print("> create_portfolio %s from upload" % portfolio.name)
    record = PyObjectDb(user_id=current_user.id, name=portfolio.name, id=portfolio.uid, type="portfolio")
    record.save_obj(portfolio)
    db_session.add(record)
    db_session.commit()
    return parse.get_portfolio_summary(portfolio)


def delete_portfolio(portfolio_id, db_session=None):
    """
    Returns all the portfolio summaries (excluding the deleted one)
    """
    if db_session is None:
        db_session = db.session
    print("> delete_portfolio %s" % portfolio_id)
    record = db_session.query(PyObjectDb).get(portfolio_id)
    record.cleanup()
    db_session.delete(record)
    db_session.commit()
    return load_portfolio_summaries()


def load_portfolio_record(portfolio_id, raise_exception=True, db_session=None, authenticate=False):
    if not db_session:
        db_session = db.session

    if authenticate:
        authenticate_current_user()

    if authenticate is False or current_user.is_admin:
        query = db_session.query(PyObjectDb).filter_by(id=portfolio_id)
    else:
        query = db_session.query(PyObjectDb).filter_by(
            id=portfolio_id, user_id=current_user.id)

    portfolio_record = query.first()

    if portfolio_record is None:
        if raise_exception:
            raise ProjectDoesNotExist(id=portfolio_record)

    return portfolio_record


def load_portfolio(portfolio_id, db_session=None):
    if db_session is None:
        db_session = db.session
    kwargs = {'id': portfolio_id, 'type': "portfolio"}
    record = db_session.query(PyObjectDb).filter_by(**kwargs).first()
    if record:
        print("> load_portfolio %s" % portfolio_id)
        return record.load()
    raise Exception("Portfolio %s not found" % portfolio_id)


def save_portfolio(portfolio, db_session=None):
    if db_session is None:
        db_session = db.session
    portfolio_id = portfolio.uid
    kwargs = {'id': portfolio_id, 'type': "portfolio"}
    query = db_session.query(PyObjectDb).filter_by(**kwargs)
    if query:
        record = query.first()
    else:
        record = PyObjectDb(user_id=current_user.id)
        record.id = UUID(portfolio_id)
        record.type = "portfolio"
        record.name = portfolio.name
    print(">> save_portfolio %s" % (portfolio_id))
    record.save_obj(portfolio)
    db_session.add(record)
    db_session.commit()


def load_portfolio_summaries(db_session=None):
    if db_session is None:
        db_session = db.session

    print("> load_portfolio_summaries")
    query = db_session.query(PyObjectDb).filter_by(user_id=current_user.id)
    portfolios = []
    for record in query:
        portfolio = record.load()
        portfolios.append(portfolio)

    summaries = map(parse.get_portfolio_summary, portfolios)

    return {'portfolios': summaries}


def rename_portfolio(portfolio_id, newName, db_session=None):
    if db_session is None:
        db_session = db.session
    portfolio = load_portfolio(portfolio_id, db_session)
    portfolio.name = newName
    save_portfolio(portfolio, db_session)
    return parse.get_portfolio_summary(portfolio)


def load_or_create_portfolio(portfolio_id, db_session=None):
    if db_session is None:
        db_session = db.session
    kwargs = {'id': portfolio_id, 'type': "portfolio"}
    record = db_session.query(PyObjectDb).filter_by(**kwargs).first()
    if record:
        print("> load_or_create_portfolio update %s" % portfolio_id)
        portfolio = record.load()
    else:
        print("> load_or_create_portfolio create %s" % portfolio_id)
        portfolio = op.Portfolio()
        portfolio.uid = UUID(portfolio_id)
        portfolio.objectives = op.defaultobjectives()
    return portfolio


def download_portfolio(portfolio_id):
    """
    Returns the (dirname, filename) of the .prj binary of the project on the server
    """
    portfolio_record = load_portfolio_record(portfolio_id, raise_exception=True)
    dirname = upload_dir_user(TEMPLATEDIR)
    if not dirname:
        dirname = TEMPLATEDIR
    filename = portfolio_record.as_portfolio_file(dirname)
    return os.path.join(dirname, filename)


def export_portfolio(portfolio_id):
    """
    Exports the results of the portfolio
    """
    portfolio_record = load_portfolio_record(portfolio_id, raise_exception=True)
    portfolio = portfolio_record.load()
    dirname = upload_dir_user(TEMPLATEDIR)
    if not dirname:
        dirname = TEMPLATEDIR
    return portfolio.export(folder=dirname)
    

def portfolio_results_ready(portfolio_id):
    """
    Checks if the portfolio is ready for export
    """
    portfolio_record = load_portfolio_record(portfolio_id, raise_exception=True)
    portfolio = portfolio_record.load()
    result = len(portfolio.results)>0
    return result


def update_portfolio_from_prt(prt_filename):
    portfolio = op.loadportfolio(prt_filename)
    create_portfolio(portfolio.name, portfolio=portfolio)
    return parse.get_portfolio_summary(portfolio)


def save_portfolio_by_summary(portfolio_id, portfolio_summary, db_session=None):
    """
    Return updated portfolio summaries
    """
    portfolio = load_or_create_portfolio(portfolio_id)
    new_project_ids = parse.set_portfolio_summary_on_portfolio(portfolio, portfolio_summary)
    for project_id in new_project_ids:
        print(">> save_portfolio_by_summary new_project_id", project_id)
        project = load_project(project_id)
        portfolio.projects[project_id] = project
    save_portfolio(portfolio, db_session)
    return load_portfolio_summaries()


def delete_portfolio_project(portfolio_id, project_id):
    """
    Return remaining portfolio summaries
    """
    portfolio = load_portfolio(portfolio_id)
    parse.delete_project_in_portfolio(portfolio, project_id)
    print(">> delete_portfolio_project %s from portfolio %s" % (project_id, portfolio_id))
    save_portfolio(portfolio)
    return load_portfolio_summaries()


def make_region_template_spreadsheet(project_id, n_region, year):
    """
    Return (dirname, basename) of the region template spreadsheet on the server
    """
    dirname = upload_dir_user(TEMPLATEDIR)
    if not dirname:
        dirname = TEMPLATEDIR
    project = load_project(project_id)
    xlsx_fname = op.makegeospreadsheet(project=project, folder=dirname, copies=n_region, refyear=year)
    return xlsx_fname


def make_region_projects(spreadsheet_fname, project_id):
    """
    Return (dirname, basename) of the region template spreadsheet on the server
    """

    project_summaries = load_current_user_project_summaries()['projects']
    existing_prj_names = [p['name'] for p in project_summaries]

    print("> make_region_projects from %s %s" % (project_id, spreadsheet_fname))
    baseproject = load_project(project_id)

    projects = op.makegeoprojects(project=baseproject, spreadsheetpath=spreadsheet_fname, dosave=False)

    prj_names = []
    for project in projects:
        print("> make_region_projects region - project %s" % project.name)
        prj_name = project.name
        i = 1
        while prj_name in existing_prj_names:
            prj_name = prj_name + ' (%d)' % i
            i += 1
        project.name = prj_name
        save_project_as_new(project, current_user.id)
        prj_names.append(prj_name)

    return { 'prjNames': prj_names }



