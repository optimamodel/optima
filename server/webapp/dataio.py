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
from hashlib import sha224

from flask import current_app, abort, request, session, make_response, jsonify
from flask_login import current_user, login_user, logout_user
from werkzeug.utils import secure_filename
from validate_email import validate_email

import optima as op
from pylab import argsort
from sciris import sanitizejson

from .dbconn import db
from . import parse
from .exceptions import ProjectDoesNotExist, ParsetAlreadyExists, \
    UserAlreadyExists, UserDoesNotExist, InvalidCredentials
from .dbmodels import UserDb, ProjectDb, ResultsDb, PyObjectDb, UndoStackDb
from .plot import make_mpld3_graph_dict, convert_to_mpld3

import six
if six.PY3: # Python 3
    basestring = str

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
    user_record_dict = {
        'id': user_record.id,
        'displayName': user_record.name,
        'username': user_record.username,
        'email': user_record.email,
        'country': user_record.country, 
        'organization': user_record.organization,
        'position': user_record.position,
        'is_admin': user_record.is_admin,
    }
    return user_record_dict


def get_user_summaries():
    raw_users = [parse_user_record(q) for q in UserDb.query.all()]
    user_names = [user['username'] for user in raw_users]
    sort_order = argsort(user_names)
    sorted_users = [raw_users[o] for o in sort_order]
    users_dict = {'users': sorted_users}
    return users_dict


def nullable_email(email_str):
    if not email_str:
        return email_str
    if validate_email(email_str):
        return email_str
    raise ValueError('{} is not a valid email'.format(email_str))


def hashed_password(password_str):
    # If we have something that looks like a hash ID, use it.
    if isinstance(password_str, basestring) and len(password_str) == 56:
        return password_str
    
    # If we have a blank string, use it.  (It's being used to specify no
    # update of the password field for update_user().)
    if password_str == '':
        return password_str
    
    # Throw an error related to an invalid password string format.
    raise ValueError(
        'Invalid password - expecting SHA224 - Received {} of length {} and type {}'.format(
            password_str, len(password_str), type(password_str)))


def parse_user_args(args):
    return {
        'email': nullable_email(args.get('email', None)),
        'name': args.get('displayName', ''),
        'username': args.get('username', ''),
        'password': hashed_password(args.get('password')),
        'country': args.get('country', ''),
        'organization': args.get('organization', ''),
        'position': args.get('position', ''),
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
    
    user_record_dict = parse_user_record(user)
    
    print('New user created: %s' % user_record_dict)

    return user_record_dict


def update_user(user_id, args):
    """
    Updates user by args and returns a user summary
    """
    user = UserDb.query.get(user_id)
    if user is None:
        raise UserDoesNotExist(user_id)

    try:    userisanonymous = current_user.is_anonymous() # Required for handling different Flask versions
    except: userisanonymous = current_user.is_anonymous

    if userisanonymous or (str(user_id) != str(current_user.id) and not current_user.is_admin):
        secret = request.args.get('secret', '')
        u = UserDb.query.filter_by(password=secret, is_admin=True).first()
        if u is None:
            abort(403)

    for key, value in args.items():
        # Skip update of the password if a '' value is passed in for it.
        if key == 'password' and value == '':
            continue
        
        # If we have a value for the key, set the appropriate field for the 
        # user record.
        if value is not None:
            setattr(user, key, value)

    db.session.commit()

    return parse_user_record(user)


def do_login_user(args):
    try:    userisanonymous = current_user.is_anonymous()  # For handling different Flask versions
    except: userisanonymous = current_user.is_anonymous

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
    return None


def grant_admin(user_id):
    ''' Grant the specified user admin rights '''
    args = {'is_admin':True}
    update_user(user_id, args)
    print('Admin rights added to user %s' % user_id)
    return None


def revoke_admin(user_id):
    ''' Grant the specified user admin rights '''
    args = {'is_admin':False}
    update_user(user_id, args)
    print('Admin rights revoked from user %s' % user_id)
    return None


def reset_password(user_id):
    ''' Reset the user's password to "optima" '''
    defaultpassword = 'optima'
    hashed_password = sha224()
    hashed_password.update(defaultpassword)
    password = hashed_password.hexdigest()
    args = {'password':password}
    update_user(user_id, args)
    print('Password for user %s reset to "%s"' % (user_id,defaultpassword))
    return None


def do_logout_current_user():
    logout_user()
    session.clear()
    return None


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
### OPTIMA DEMO PROJECTS
#############################################################################################

def get_optimademo_user(name='_OptimaDemo', die=False):
    ''' Get the Optima Demo user ID, from its name -- default is '_OptimaDemo' '''
    user = UserDb.query.filter_by(username=name).first()
    if user is None:
        errormsg = 'WARNING, no Optima demo user found; demo projects not available' # Could quote name, but (minor) security risk
        if die: raise Exception(errormsg)
        else:   print(errormsg)
        return None
    else:
        return user.id


def get_optimademo_projects(die=False):
    '''
    Return the projects associated with the Optima Demo user.
    
    Note that these should be stored in the analyses repo under the name optimademo.    
    '''
    try: # Try to load the demo projects...
        user_id = get_optimademo_user()
        query = ProjectDb.query.filter_by(user_id=user_id)
        projectlist = map(load_project_summary_from_project_record, query.all())
        sortedprojectlist = sorted(projectlist, key=lambda proj: proj['name']) # Sorts by project name
        demoprojectlist = []
        nationalprojectlist = []
        regionalprojectlist = []
        for proj in sortedprojectlist:
            if   proj['name'].find('(demo)')>=0:   demoprojectlist.append(proj) # It's a demo project
            elif proj['name'].find('regional')>=0: regionalprojectlist.append(proj) # It's a regional project
            else:                                  nationalprojectlist.append(proj)
        projects = demoprojectlist + regionalprojectlist + nationalprojectlist # Combine project lists into one sorted list
    except Exception as E: # But just skip creation if that fails
        errormsg = 'WARNING, could not load demo projects: %s' % repr(E)
        if die: raise Exception(errormsg)
        else:   print(errormsg)
        projects = []
    output = {'projects': projects}
    return output



#############################################################################################
### PROJECT
#############################################################################################

def load_project_record(project_id, raise_exception=True, db_session=None, authenticate=False):
    if db_session is None:
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
    if db_session is None:
        db_session = db.session
    project_record = load_project_record(project.uid, db_session=db_session)
    # Copy the project, only save what we want...
    new_project = op.dcp(project)
    new_project.spreadsheet = None
    if is_skip_result:
        new_project.results = op.odict()
    project_record.save_obj(project)
    db_session.add(project_record)
    db_session.commit()


def load_project_from_record(project_record):
    try:
        project = project_record.load()
    except:
        print('WARNING, could not load project!')
        return None
    for progset in project.progsets.values():
        if not hasattr(progset, 'inactive_programs'):
            progset.inactive_programs = op.odict()
    project.restorelinks()
    return project


def load_project(project_id, raise_exception=True, db_session=None, authenticate=True):
    if db_session is None:
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
    project.modified = op.today()
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
    project.uid = project_entry.id
    save_project(project)

    new_project_template = secure_filename("%s.xlsx" % project_summary['name'])
    path = templatepath(new_project_template)
    op.makespreadsheet(path, pops=project_summary['populations'], datastart=project_summary['startYear'], dataend=project_summary['endYear'])

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
    project.uid = project_entry.id
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
    print(">> download_data_spreadsheet init")
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
        project.makespreadsheet(filename=path)
    return path


def save_project_as_new(project, user_id):
    # Create a new Postgres projects table record, and add and flush it.
    project_record = ProjectDb(user_id)
    db.session.add(project_record)
    db.session.flush()

    print(">> save_project_as_new '%s'" % project.name)
    
    # Set the UID of the Project object passed in to the UID created in the 
    # new Postgres record.
    project.uid = project_record.id
    
    # For each of the embedded Resultsets...
    for result in project.results.values():
        # Grab the result name.
        name = result.name
        
        # Set a new UID to be used for the DB entries.
        result.uid = op.uuid()
        
        # For results that should be cached, create or update a Postgres 
        # record for the result.
        if 'scenarios' in name: 
            update_or_create_result_record_by_id(result, project.uid, None, 'scenarios')
        if 'optim' in name:     
            update_or_create_result_record_by_id(result, project.uid, None, 'optimization')
        if 'parset' in name:   
            try:    parset_uid = project.parsets[result.parsetname].uid # Try to get this, but don't worry if it fails
            except: parset_uid = None
            update_or_create_result_record_by_id(result, project.uid, parset_uid, 'calibration')
            
    # Commit the Postgres changes.
    db.session.commit()
    
    # Save the changed Project object to Redis.
    save_project(project)
    
    return None


def copy_project(project_id, new_project_name):
    """
    Returns the project_id of the copied project
    """
    print(">> copy_project args project_id %s" % project_id)
    print(">> copy_project args new_project_name %s" % new_project_name)     
    
    # Get the Project object for the project to be copied.
    project_record = load_project_record(project_id, raise_exception=True)
    project = load_project_from_record(project_record)
    
    # Just change the project name, and we have the new version of the 
    # Project object to be saved as a copy.
    project.name = new_project_name
    
    # Set the user UID for the new projects record to be the current user.
    user_id = current_user.id 
    
    # Save a Postgres projects record for the copy project.
    save_project_as_new(project, user_id)

    # Grab a dictionary of parset UIDs, pointing to names for each.
    # This line is not neessary if the block below is removed.
    #parset_name_by_id = {parset.uid: name for name, parset in project.parsets.items()}
    
    # Remember the new project UID (created in save_project_as_new()).
    copy_project_id = project.uid

    # I'm not convinced any of this code below is necessary to the 
    # functionality of project copying, and it frequently causes extra 
    # Postgres results records to be created that are just copies of the 
    # Postgres records made from the Resultsets embedded in the Project 
    # objects.  At worst, 1 runsim() ends up getting done when a copy of a 
    # cached result is missing. [GLC, 6/26/17]
#    # Copy each matching Postgres results record to a new record.
#    
#    # Grab all of the Postgres results records matching the project record.
#    result_records = project_record.results
#    
#    # If any results match...
#    if result_records:
#        # For each matching recsult record...
#        for result_record in result_records:
#            # reset the parset_id in results to new project
#            
#            # Load the Result object from the record.
#            result = result_record.load()
#            
#            # Pull the parset ID from the record's UID.
#            parset_id = result_record.parset_id
#            
#            # If the old project lacks the record UID, skip over this result 
#            # record.  We don't want to copy it.
#            if parset_id not in parset_name_by_id:
#                continue
#            
#            # Get the parset name matching what's in the Project object.
#            parset_name = parset_name_by_id[parset_id]
#            
#            # Get a list of all matching parsets where the name matches what 
#            # we are looking for.
#            new_parset = [r for r in project.parsets.values() if r.name == parset_name]
#            
#            # If there is no match, skip this results record.  We don't want 
#            # to copy it.
#            if not new_parset:
#                continue
#            
#            # Get the parset UID just of the first match.
#            copy_parset_id = new_parset[0].uid
#
#            # Create a new results record for the copy project for this results 
#            # record from the old project.
#            copy_result_record = ResultsDb(
#                copy_parset_id, copy_project_id, result_record.calculation_type)
#            
#            # Add and flush the new record to Postgres.
#            db.session.add(copy_result_record)
#            db.session.flush()
#
#            # Write out the result with new UID to Redis.
#            result.uid = copy_result_record.id
#            copy_result_record.save_obj(result)

    # Commit the Postgres changes.
    db.session.commit()

    # Return the UID for the new projects record.
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
    try:
        project = op.loadproj(prj_filename)
    except Exception:
        return { 'projectId': 'BadFileFormatError' }
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
    server_filename = project.save(filename=project.name, folder=dirname, saveresults=False)
    print(">> download_project %s" % (server_filename))
    return server_filename


def download_project_with_result(project_id):
    """
    Returns the filename of the .prj binary of the project on the server
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
    server_filename = project.save(filename=project.name, folder=dirname, saveresults=True)
    print(">> download_project_with_result %s" % (server_filename))
    return server_filename


def update_project_from_uploaded_spreadsheet(spreadsheet_fname, project_id):
    def modify(project):
        project.loadspreadsheet(spreadsheet_fname, name='default', overwrite=True, makedefaults=True)
    update_project_with_fn(project_id, modify)
    return { 'success': True }


def load_zip_of_prj_files(project_ids):
    """
    Returns the (dirname, filename) of the .zip of the selected projects on the server
    """
    dirname = upload_dir_user(TEMPLATEDIR)
    if not dirname:
        dirname = TEMPLATEDIR

    prjs = [load_project_record(id).as_file(dirname) for id in project_ids]

    datestr = op.today().strftime('%Y%b%d_%H%M%S').encode('ascii', 'ignore') # Today's date
    zip_fname = 'Optima_projects_%s.zip' % datestr
    server_zip_fname = os.path.join(dirname, zip_fname)
    with ZipFile(server_zip_fname, 'w') as zipfile:
        for prj in prjs:
            zipfile.write(os.path.join(dirname, prj), 'portfolio/{}'.format(prj))

    full_filename = os.path.join(dirname, zip_fname)
    return full_filename


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

    is_change = is_change

    return is_change


def get_server_filename(basename):
    dirname = upload_dir_user(TEMPLATEDIR)
    if not dirname:
        dirname = TEMPLATEDIR
    return os.path.join(dirname, op.sanitizefilename(basename))


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
    try:
        obj = op.loadobj(filename)
        if obj_type == "parset":
            project.addparset(parset=obj, overwrite=True)
        elif obj_type == "progset":
            project.addprogset(progset=obj, overwrite=True)
        elif obj_type == "scenario":
            project.addscen(scen=obj, overwrite=True)
        elif obj_type == "optimization":
            project.addoptim(optim=obj, overwrite=True)
    except Exception:
        return { 'name': 'BadFileFormatError' }
    save_project(project)
    return { 'name': obj.name }



#############################################################################################
### RESULTS
#############################################################################################

def load_result(project_id, which=None, name=None):
    result_records = db.session.query(ResultsDb).filter_by(project_id=project_id)
    for result_record in result_records:
        result = result_record.load()
        if result.name == name:
            print(">> load_result loaded '%s'" % str(result.name))
            if which:
                result.which = which
                print(">> load_result saving which", which)
                result_record.save_obj(result)
            return result
    print(">> load_result: stored result is empty")
    return None


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

    print(">> update_or_create_result_record_by_id args project_id %s" % project_id)
    print(">> update_or_create_result_record_by_id args parset_id %s" % parset_id)
    result_record = db_session.query(ResultsDb).get(result.uid)
    if result_record is not None:
        print(">> update_or_create_result_record_by_id update '%s'" % (result.name))
    else:
        result_record = ResultsDb(
            parset_id=parset_id,
            project_id=project_id,
            calculation_type=calculation_type)
        print(">> update_or_create_result_record_by_id create '%s'" % (result.name))

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
    
    
def delete_result_by_project_id(
        project_id, db_session=None):
    if db_session is None:
        db_session = db.session

    records = db_session.query(ResultsDb).filter_by(project_id=project_id)
    for record in records:
        print(">> delete_result_by_project_id '%s'" % project_id)
        record.cleanup()
        db_session.delete(record)
    db_session.commit()
    

def download_result_data(result_id):
    """
    Returns (dirname, basename) of the the result.csv on the server
    """
    dirname = upload_dir_user(TEMPLATEDIR)
    if not dirname:
        dirname = TEMPLATEDIR
    result = load_result_by_id(result_id)
    return result.export(folder=dirname)


def load_result_by_optimization(project, optimization):

    result_name = "optim-" + optimization.name
    try:
        parset_id = project.parsets[optimization.parsetname].uid # Try to extract the 
    except:
        print('>> Warning, optimization parset "%s" not in project parsets: %s; reverting to default "%s"' % (optimization.parsetname, project.parsets.keys(), project.parset().name))
        parset_id = project.parset().uid # Just get the default

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
    # Super kludgy, advanced switch gets stuck here instead of in a separate variable
    if 'advanced' in which:
#        advanced = True
        which.remove("advanced")
    
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


def refresh_parset(project_id, parset_id, resetprevalence):
    ''' Refresh parset from data '''
    
    def update_project_fn(project):
        parset = parse.get_parset_from_project(project, parset_id)
        parset_name = parset.name
        project.refreshparset(name=parset_name, resetprevalence=resetprevalence)

    update_project_with_fn(project_id, update_project_fn)
    delete_result_by_parset_id(project_id, parset_id)
    return None


def fixproptx(project_id, parset_id, fix=None):
    ''' Toggle whether or not proportion of people on ART is fixed '''
    def update_project_fn(project):
        parset = parse.get_parset_from_project(project, parset_id)
        parset.fixprops(fix=fix) # Update the proportions

    update_project_with_fn(project_id, update_project_fn)
    delete_result_by_parset_id(project_id, parset_id)
    return None

def fixproptx_on(project_id, parset_id):
    ''' Turn on constant proportion on ART '''
    fixproptx(project_id, parset_id, fix=True)
    return None

def fixproptx_off(project_id, parset_id):
    ''' Turn off constant proportion on ART '''
    fixproptx(project_id, parset_id, fix=False)
    return None

def get_isfixed(project_id, parset_id):
    ''' Read whether constant proportion is off or on for ART '''
    project = load_project(project_id)
    parset = parse.get_parset_from_project(project, parset_id)
    return {"isfixed": parset.isfixed}

def load_parset_summaries(project_id):
    project = load_project(project_id)
    return {"parsets": parse.get_parset_summaries(project)}


def load_project_parameters(project_id):
    return {'parameters': parse.get_parameters_for_edit_program(load_project(project_id)) }


def load_parameters_from_progset_parset(project_id, progset_id, parset_id):
    project = load_project(project_id)
    return parse.get_parameters_for_outcomes(project, progset_id, parset_id)


def load_parameters(project_id, parset_id, advanced=False):
    project = load_project(project_id)
    parset = parse.get_parset_from_project(project, parset_id)
    return parse.get_parameters_from_parset(parset, advanced=advanced)


def save_parameters(project_id, parset_id, parameters):

    def update_project_fn(project):
        parset = parse.get_parset_from_project(project, parset_id)
        parset.modified = op.today()
        parse.set_parameters_on_parset(parameters, parset)

    delete_result_by_parset_id(project_id, parset_id)
    update_project_with_fn(project_id, update_project_fn)



def load_parset_graphs(project_id, parset_id, calculation_type, which=None, parameters=None, advanced_pars=None, zoom=None, startYear=None, endYear=None):

    print(">> load_parset_graphs args project_id %s" % project_id)
    print(">> load_parset_graphs args parset_id %s" % parset_id)
    print(">> load_parset_graphs args calculation_type %s" % calculation_type)
    project = load_project(project_id)
    parset = parse.get_parset_from_project(project, parset_id)

    result_name = "parset-" + parset.name
    print(">> load_parset_graphs result-name '%s'" % result_name)
    result = load_result(project_id, name=result_name, which=which)
    if result:
        if not which:
            if hasattr(result, 'which'):
                print(">> load_parset_graphs load stored which of parset '%s'" % parset.name)
                which = result.which

    if parameters is not None:
        print(">> load_parset_graphs updating parset '%s'" % parset.name)
        parset.modified = op.today()
        parset.start    = startYear
        parset.end      = endYear
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
        "parameters": parse.get_parameters_from_parset(parset, advanced=advanced_pars),
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
    return sanitizejson(dict(zip(years, popsizes)))


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


def create_default_progset(project_id, new_progset_name):

    def update_project_fn(project):
        project.addprogset(name=new_progset_name)
        project.progsets[new_progset_name].uid = op.uuid()

    update_project_with_fn(project_id, update_project_fn)
    return load_progset_summaries(project_id)


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
        'budgets': sanitizejson(budgets),
        'pars': sanitizejson(pars),
    }


def launch_reconcile_calc(project_id, progset_id, parset_id, year, maxtime):
    import server.webapp.tasks as tasks
    print(">> launch_reconcile_calc")
    calc_status = tasks.launch_reconcile(project_id, progset_id, parset_id, year, maxtime)
    return calc_status



#############################################################################################
### SCENARIOS
#############################################################################################


def make_scenarios_graphs(project_id, which=None, is_run=False, zoom=None, startYear=None, endYear=None):
    result = load_result(project_id, name="scenarios", which=which)

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
    
    print('save_optimization_summaries() for %s' % project_id)
    print('%s' % optimization_summaries)
    
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


def load_optimization_graphs(project_id=None, optim_name=None, which=None, zoom=None, startYear=None, endYear=None):
    project = load_project(project_id)
    optimization = project.optims[optim_name]
    result_name = optimization.resultsref # Use result name stored in the optimization
    print(">> load_optimization_graphs results_name %s" % result_name)
    result = load_result(project.uid, name=result_name, which=which)
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
    if db_session is None:
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
    try:
        portfolio = op.loadportfolio(prt_filename)
        create_portfolio(portfolio.name, portfolio=portfolio)
    except Exception:
        return { 'created': 'BadFileFormatError' }
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
        project.name = get_unique_name(project.name, portfolio.projects.keys()) # Ensure the name is unique
        portfolio.projects[project.name] = project
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

    try:
        projects = op.makegeoprojects(project=baseproject, spreadsheetpath=spreadsheet_fname, dosave=False)
    except Exception:
        return { 'prjNames': 'BadFileFormatError' }

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



#############################################################################################
### UNDO STACKS
#############################################################################################

class UndoStack(object):
    """
    A stack of Project objects for allowing Undo and Redo functionality in 
    Optima.
    
    Methods:
        __init__(theProjectUID: UUID): void -- constructor, taking the project's 
            UID
        pushNewVersion(newVersion: Project): bool -- if we can, push a Project 
            object as a new save version on the stack and return True; 
            otherwise return False
        getUndoVersion(): Project -- index the stack back to the previous 
            version and return the Project object saved there
        getRedoVersion(): Project -- index the stack forward to the next 
            version and return the Project object saved there
        getSelectedVersion(): Project -- return the Project object saved in 
            the selected stack entry
        getProjectUID(): UUID -- returns the project UID
        isDirty(): bool -- is there pending data to be saved?
        isClean(): bool -- is there no pending data yet to be saved?
        setDirtyFlagUse(useDirtyFlag: bool): void -- sets whether the stack 
            uses the dirty flag or not
        setDirty(): void -- set the dirty flag dirty
        setClean(): void -- set the dirty flag clean
        canSave(): void -- can we save to this stack?
        canUndo(): bool -- can we do an Undo from this stack?
        canRedo(): bool -- can we do an Redo from this stack? 
        isEmpty(): bool -- is the stack empty?
        atStackTop(): bool -- are we at the top of the stack (latest version)?
        atStackBottom(): bool -- are we at the bottom of the stack (oldest version)?
        showContents(): void -- print out the contents of the stack
                    
    Attributes:
        projectUID: UUID -- UID of the project, indexing the Postgres and 
            Redis tables
        useDirtyFlag: bool -- should we use the dirty flag?
        dirtyFlag: bool -- do we have pending information waiting to be saved?
        projectVersions: list of Project objects -- Python list holding 
            the Project objects we want to be able to revert to
        currentIndex: int [or None] -- the index into the current project 
            version on the stack
        
    Usage:
        >>> undoStack = UndoStack(project_id)                      
    """
    
    def __init__(self, theProjectUID):
        # Set up the project UID we pass in.
        self.projectUID = theProjectUID 
        
        # Set the dirtyFlag to be used to start with.
        self.setDirtyFlagUse(True)
        
        # Set the dirtyFlag to clean.
        self.setClean()
        
        # Start with an empty list of Projects and index None.
        self.projectVersions = []
        self.currentIndex = None       
        
    def pushNewVersion(self, newVersion):
        # Exit if we cannot save to the stack yet.
        if not self.canSave():
            return False
        
        # If we are not at the stack top, trim out all indices after the 
        # current one.
        if not self.atStackTop():
            self.projectVersions = self.projectVersions[:(self.currentIndex + 1)]
            
        # Append the Project object for the new version.
        self.projectVersions.append(newVersion)
        
        # Move the index up so we point to the new version.
        if self.currentIndex == None:
            self.currentIndex = 0
        else:
            self.currentIndex += 1
            
        # Set the dirty flag clean.
        self.setClean()
        
        # Return success.
        return True
    
    def getUndoVersion(self):
        # Exit if we cannot undo from the stack yet.
        if not self.canUndo():
            return None
        
        # If we are using the dirty flag...
        if self.useDirtyFlag:
            # If we have stuff pending to save, set the clean flag and 
            # return the current version.
            if self.isDirty():
                self.setClean()
                return self.getSelectedVersion()
            
            # If nothing is pending to save...
            else:
                # Move the index back to the previous version.
                self.currentIndex -= 1
                
                # Return the now-pointed-to version of the Project.
                return self.projectVersions[self.currentIndex]
        
        # Otherwise (not using the dirty flag)...
        else:
            # Move the index back to the previous version.
            self.currentIndex -= 1
            
            # Return the now-pointed-to version of the Project.
            return self.projectVersions[self.currentIndex]
    
    def getRedoVersion(self):
        # Exit if we cannot redo from the stack yet.
        if not self.canRedo():
            return None
        
        # Move the index forward to the next version.
        self.currentIndex += 1
        
        # Set the clean flag.  (We'll lose any changes pending for saving.)
        self.setClean()
        
        # Return the now-pointed-to version of the Project.
        return self.projectVersions[self.currentIndex]
    
    def getSelectedVersion(self):
        return self.projectVersions[self.currentIndex]
    
    def getProjectUID(self):
        return self.projectUID
    
    def isDirty(self):
        return self.dirtyFlag
    
    def isClean(self):
        return not self.dirtyFlag
    
    def setDirtyFlagUse(self, useDirtyFlag):
        self.useDirtyFlag = useDirtyFlag
        
    def setDirty(self):
        self.dirtyFlag = True
    
    def setClean(self):
        self.dirtyFlag = False
        
    def canSave(self):
        # You can only save to the stack if the dirty flag is not being used or 
        # it is set.
        if not self.useDirtyFlag:
            return True
        else:
            return self.isDirty()
    
    def canUndo(self):
        # If we don't have a valid index, we can't undo.
        if self.currentIndex is None:
            return False
        
        # If we are using the dirty flag...
        if self.useDirtyFlag:
            # If the dirty flag is clean, we can undo only if we are at least 
            # one stack entry from the bottom.
            if self.isClean():
                return self.currentIndex > 0
            
            # Otherwise (dirty flag dirty), we're good just by having a valid 
            # index.
            else:
                return True            
            
        # Otherwise (we're not using dirty flag), we're good only if we are 
        # at least one stack entry from the bottom.
        else:
            return self.currentIndex > 0
    
    def canRedo(self):
        return (not self.atStackTop())
    
    def isEmpty(self):
        return len(self.projectVersions) == 0
    
    def atStackTop(self):
        if self.currentIndex == None:
            return True
        else:
            return (self.currentIndex == (len(self.projectVersions) - 1))
        
    def atStackBottom(self):
        return self.currentIndex == 0
        
    def showContents(self):
        print('Undo Stack Contents')
        print('-------------------')
        print("Project UID: '%s'" % self.projectUID)
        if self.useDirtyFlag:
            print('Uses Dirty Flag?: Yes')
            if self.dirtyFlag:
                print('Dirty Flag State: Dirty')
            else:
                print('Dirty Flag State: Clean')
        else:
            print('Uses Dirty Flag?: No')
        if self.isEmpty():
            print('Contents: Empty')
        else:
            print('Contents: %d Project versions' % len(self.projectVersions))
            print('Stack Index: %d' % self.currentIndex)
        print
        

def load_undo_stack(project_id):
    print(">> load_undo_stack project_id %s" % project_id)
    
    # Pull out all undo_stacks rows with matching Project UIDs.
    undo_stack_records = db.session.query(UndoStackDb).filter_by(project_id=project_id)
    
    # For each match, go until we find the first Project UID match.  (There 
    # should only be one.)
    for undo_stack_record in undo_stack_records:
        # Pull the UndoStack object out of Redis.
        undoStack = undo_stack_record.load()
        
        # If we have a valid match of the project UID in the UndoStack object, 
        # return the UndoStack object.
        if undoStack.getProjectUID() == project_id:
            print(">> load_undo_stack loaded '%s'" % project_id)
            return undoStack
        
    # Failure, return no match.
    print(">> load_undo_stack: no matching undo_stacks entry")
    return None


def update_or_create_undo_stack_record(undoStack, project_id, db_session=None):
    print(">> update_or_create_undo_stack project_id '%s'" % project_id)
    
    # If no session is passed in, grab the db module one.
    if db_session is None:
        db_session = db.session
  
    # Pull out the first undo_stacks row with Project UID matching project_id.
    undo_stack_record = db_session.query(UndoStackDb).filter_by(project_id=project_id).first()
    
    # If we have no matches, create a new record to be added, and give it a 
    # new UID.
    if undo_stack_record is None:
        print(">> update_or_create_undo_stack create '%s'" % project_id)
        undo_stack_record = UndoStackDb(project_id=project_id)
        undo_stack_record.id = op.uuid()
        
    # Otherwise, just denote an update.
    else:
        print(">> update_or_create_undo_stack update '%s'" % project_id)
            
    # Write the UndoStack object to Redis.
    undo_stack_record.save_obj(undoStack)
    
    # Add the updated or created undo_stacks record.
    db_session.add(undo_stack_record)
    
    # Commit the database session.
    db_session.commit()


def delete_undo_stack_record(project_id, db_session=None):
    print(">> delete_undo_stack_record project_id %s" % project_id)
    
    # If no session is passed in, grab the db module one.    
    if db_session is None:
        db_session = db.session
        
    # Pull out all undo_stacks rows with Project UID matching project_id.
    undo_stack_records = db_session.query(UndoStackDb).filter_by(project_id=project_id)

    # Call the cleanup for each record (i.e., deleting the Redis entries).
    for undo_stack_record in undo_stack_records:
        undo_stack_record.cleanup()
        
    # Delete all of the matching records.
    undo_stack_records.delete()
    
    # Commit the database session.
    db_session.commit()
    
    
def delete_undo_stack_zombie_records(db_session=None):
    print(">> delete_undo_stack_zombie_records")
    
    # If no session is passed in, grab the db module one.    
    if db_session is None:
        db_session = db.session  
        
    # Pull out all undo_stacks rows with NULL Project UID.
    undo_stack_records = db_session.query(UndoStackDb).filter_by(project_id=None)

    # Call the cleanup for each record (i.e., deleting the Redis entries).
    for undo_stack_record in undo_stack_records:
        undo_stack_record.cleanup()
        
    # Delete all of the matching records.
    undo_stack_records.delete()
    
    # Commit the database session.
    db_session.commit()

    
def init_new_undo_stack(project_id):
    """
    Given a project UID, if we have a valid project record, set up a new 
    UndoStack object, create or update an undo_stacks (Postgres) record for it, 
    and return True; return False otherwise.
    
    Args:
        project_id: UID of the project
        
    Returns:
        True if the project gets written to a new UndoStack, False otherwise
    """   
    print(">> init_new_undo_stack project_id '%s'" % project_id)

    # Load the Project object from the UID.
    project = load_project(project_id)
    
    # If we don't have a valid project, return a failure.
    if project is None:
        return { 'updatedundostack': False }
        
    # Create a new UndoStack object which is empty and owned by the UID.
    undoStack = UndoStack(project_id)
    
    # Turn off the use of the dirty flag.
    undoStack.setDirtyFlagUse(False)
    
    # Push the project object to the UndoStack, so we have the first save in it.
    undoStack.pushNewVersion(project)
    
    # Update the undo_stacks entry (including the Redis stored data).
    update_or_create_undo_stack_record(undoStack, project_id)
    
    # Return success.
    return { 'updatedundostack': True }


def push_project_to_undo_stack(project_id):
    """
    Given a project UID, if the UndoStack has an ID match, load the Project 
    object and push it to the UndoStack.
    
    Args:
        project_id: UID of the project
        
    Returns:
        True if a successful push is done, False otherwise           
    """
    print(">> push_project_to_undo_stack project_id '%s'" % project_id)
    
    # Load the Project object from the UID.
    project = load_project(project_id)
    
    # If we don't have a valid project, return a failure.
    if project is None:
        return { 'didpush': False }
    
    # Load the saved UndoStack object indexed by the project UID.
    undoStack = load_undo_stack(project_id)     
    
    # If we cannot save to the Undo stack, return a failure.
    if not undoStack.canSave():
        return { 'didpush': False }
    
    # Push the project to the stack.
    undoStack.pushNewVersion(project)
    
    # Update the undo_stacks entry (including the Redis stored data).
    update_or_create_undo_stack_record(undoStack, project_id)
    
    # Return success.
    return { 'didpush': True }


def fetch_undo_project(project_id):
    """
    Given a project UID, if the UndoStack has an ID match, and it can do a 
    valid Undo, grab the appropriate Project object and update Postgres and 
    Redis and return True; otherwise return False.
    
    Args:
        project_id: UID of the project
        
    Returns:
        True if a successful undo is done, False otherwise    
    """
    print(">> fetch_undo_project project_id '%s'" % project_id)
    
    #return unit_test_build_undo_stack(project_id, useDirtyFlag=False)

    # Load the saved UndoStack object indexed by the project UID.
    undoStack = load_undo_stack(project_id) 
    
    # If we cannot do an undo on the Undo stack, return a failure.
    if not undoStack.canUndo():
        return { 'didundo': False }
    
    # Pull out the Undo version of the project and update the stack.
    project = undoStack.getUndoVersion()
    
    # If we don't have a valid project, return a failure.
    if project is None:
        return { 'didundo': False }  
    
    # Save the withdrawn version of the project to the databases.
    save_project(project)
    
    # Update the undo_stacks entry (including the Redis stored data).
    update_or_create_undo_stack_record(undoStack, project_id)
    
    # Delete any result records with the corresponding project UID.  This 
    # will force the client to rerun the simulation rather than mistakenly
    # using the cached result for the graphs.
    delete_result_by_project_id(project_id)
    
    # Return success.
    return { 'didundo': True }


def fetch_redo_project(project_id):
    """
    Given a project UID, if the UndoStack has an ID match, and it can do a 
    valid Redo, grab the appropriate Project object and update Postgres and 
    Redis and return True; otherwise return False.
    
    Args:
        project_id: UID of the project
        
    Returns:
        True if a successful redo is done, False otherwise      
    """
    print(">> fetch_redo_project project_id '%s'" % project_id)
    
    #unit_test_show_and_delete_undo_stack(project_id)
    
    # Load the saved UndoStack object indexed by the project UID.
    undoStack = load_undo_stack(project_id)
    
    # If we cannot do an redo on the Undo stack, return a failure.
    if not undoStack.canRedo():
        return { 'didredo': False } 
    
    # Pull out the Redo version of the project and update the stack.
    project = undoStack.getRedoVersion() 
    
    # If we don't have a valid project, return a failure.
    if project is None:
        return { 'didredo': False }  
    
    # Save the withdrawn version of the project to the databases.
    save_project(project)
    
    # Update the undo_stacks entry (including the Redis stored data).
    update_or_create_undo_stack_record(undoStack, project_id)
    
    # Delete any result records with the corresponding project UID.  This 
    # will force the client to rerun the simulation rather than mistakenly
    # using the cached result for the graphs.
    delete_result_by_project_id(project_id)
    
    # Return success.
    return { 'didredo': True }


def unit_test_build_undo_stack(project_id, useDirtyFlag=True):
    def push_new_version(project, useDirtyFlag=True):
        # Set the dirty flag to enable pushing if it's needed.
        if useDirtyFlag:
            # Set the dirty flag.
            set_dirty_flag_dirty()
            
        # Show whether we can save to the stack or not.
        if undoStack.canSave():
            print('Can we save to the stack?: Yes')
            print
        else:
            print('Can we save to the stack?: No')
            print()
            
        # Try to push the project to the stack.
        undoStack.pushNewVersion(project)
        
        # Tell what we've done.
        print('Pushed version...')
        print()
        
        # Show undoStack contents.
        undoStack.showContents()
        
    def do_undo():
        # Show whether we can undo from the stack or not.
        if undoStack.canUndo():
            print('Can we do an Undo on this stack?: Yes')
            print
        else:
            print('Can we do an Undo on this stack?: No')
            print()
            
        # Try to push the project to the stack.
        project = undoStack.getUndoVersion()
        
        # Tell what we've done.
        print('Got Undo version...')
        print
        
        # Show undoStack contents.
        undoStack.showContents()
        
        # Return the project.
        return project
        
    def do_redo():
        # Show whether we can redo from the stack or not.
        if undoStack.canRedo():
            print('Can we do an Redo on this stack?: Yes')
            print
        else:
            print('Can we do an Redo on this stack?: No')
            print()
            
        # Try to push the project to the stack.
        project = undoStack.getRedoVersion()
        
        # Tell what we've done.
        print('Got Redo version...')
        print
        
        # Show undoStack contents.
        undoStack.showContents() 
        
        # Return the project.
        return project
    
    def set_dirty_flag_dirty():
        # Set the dirty flag.
        undoStack.setDirty()
        
        # Tell what we've done.
        print('Set the dirty flag dirty...')
        print
        
        # Show undoStack contents.
        undoStack.showContents()
        
    def set_dirty_flag_clean():
        # Set the dirty flag.
        undoStack.setClean()
        
        # Tell what we've done.
        print('Set the dirty flag clean...')
        print
        
        # Show undoStack contents.
        undoStack.showContents() 
        
    print(">> unit_test_build_undo_stack project_id '%s'" % project_id)
    
    # Load the Project object from the UID.
    project = load_project(project_id)
    
    # Create a new UndoStack object which is empty and owned by the UID.
    undoStack = UndoStack(project_id)
    
    # Tell what we've done.
    print('Created initial UndoStack...')
    print()
    
    # Set whether we want to use the dirty flag.
    undoStack.setDirtyFlagUse(useDirtyFlag)
    
    # Tell what we've done.
    print('Set up whether to use dirty flag or not...')
    print()
    
    # Show undoStack contents.
    undoStack.showContents()
    
    # Perform tests.
    push_new_version(project, useDirtyFlag)
    push_new_version(project, useDirtyFlag)
    push_new_version(project, useDirtyFlag)
    push_new_version(project, useDirtyFlag)
    do_undo()
    do_undo()
    do_redo()
    do_undo()
    do_undo()
    push_new_version(project, useDirtyFlag)
            
    # Update the undo_stacks entry (including the Redis stored data).
    update_or_create_undo_stack_record(undoStack, project_id)


def unit_test_show_and_delete_undo_stack(project_id):
    print(">> unit_test_show_and_delete_undo_stack project_id '%s'" % project_id)
    
    # Load the saved UndoStack object indexed by the project UID.
    undoStack = load_undo_stack(project_id)
    
    # If we succeeded, give a message and show the contents, then delete the 
    # entry.
    if undoStack is not None:
        print('>> unit_test_show_and_delete_undo_stack: undoStack successfully loaded.')
        undoStack.showContents()
        delete_undo_stack_record(project_id)
        
    # Otherwise, 
    else:
        print('>> unit_test_show_and_delete_undo_stack: undoStack did not load!')
    
