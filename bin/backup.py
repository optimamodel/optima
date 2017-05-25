import requests
import sys
import os
import json
from hashlib import sha224
from pylab import argsort
try:    import optima as op
except: pass
import datetime


def safemkdir(*args):
    ''' Skip exceptions and handle join() '''
    try:    os.makedirs(os.path.join(*args))
    except: pass
    return None
    

def downloadprojects(password=None, savelocation=None, server=None, username=None, overwrite=False):
    '''
    A utility for downloading all projects from an Optima 2.0+ server for an admin account.

    Here's how to use it with the defaults for 'admin' at hiv.optimamodel.com, saving to folder optimaprojects:

         python downloadprojects.py <password> <savelocation>

    Version: 2017may23
    '''
    
    # Define defaults
    if username is None:     username     = 'admin'
    if password is None:     password     = 'zzz'
    if savelocation is None: savelocation = 'optimaprojects'
    if server is None:       server       = 'http://localhost:8080'
    
    # Try timing, but don't try too hard
    try:    T = op.tic()
    except: pass
    
    print('Starting HTTP sesion...')
    session = requests.Session()

    print('Logging in as %s...' % (username,))
    hashed_password = sha224()
    hashed_password.update(password)
    password = hashed_password.hexdigest()

    print('Logging into server...')
    response = session.post(server + '/api/user/login', json={'username': username, 'password': password})
    if not response.status_code == 200:
        print('Failed login:\n%s' % response.content)
        sys.exit(1)
    print('Logged in as %s on %s' % (response.json()['username'], server))

    print('Downloading user list...')
    safemkdir(savelocation)
    users = session.get(server + '/api/user').json()['users']['users']
    f = open(os.path.join(savelocation, 'users.json'), 'w')
    json.dump(users, f, indent=2)
    username_by_id = {}
    for user in users:
        username_by_id[user['id']] = user['username']

    print('Downloading project list, please be patient...')
    url = server + '/api/procedure'
    payload = {'name': 'load_all_project_summaries'}
    projects = session.post(url, data=json.dumps(payload)).json()['projects']

    print('Processing projects...')
    success = []
    failed = []
    projectnames = []
    usernames = []
    combined = []
    for project in projects:
        try:
            username    = username_by_id[project['userId']] # Pull out the user names
            projectname = project['name'] # Pull out the project names
            usernames.append(username)
            projectnames.append(projectname)
            combined.append(username+projectname) # Make a key by combining them
        except:
            try: failedname = str(project)
            except: failedname = 'Could not even append string representation, what the hell'
            print('WARNING, the following project failed: %s' % failedname)
            failed.append(failedname)
    
    print('Sorting projects by user...')
    order = argsort(combined) # Figure out the alphabetical order
    sortedusernames = []
    sortedprojectnames = []
    for o in order:
        sortedusernames.append(usernames[o])
        sortedprojectnames.append(projectnames[o])
    
    print('Downloading all projects...')
    nprojects = len(sortedprojectnames)
    for i in range(nprojects):
        username = sortedusernames[i]
        projectname = sortedprojectnames[i]
        try:
            print('  Downloading user "%s" project "%s" (%i/%i)' % (username, projectname, i+1, nprojects))
    
            dirname = os.path.join(savelocation, username)
            safemkdir(dirname)
    
            fname = os.path.join(dirname, projectname+'.prj')
            while os.path.isfile(fname):
                if overwrite:  print('    Downloaded already, overwriting...')
                else:          fname += '.new' # Just keep appending till the cows come home
            try:
                url = server + '/api/download'
                payload = {'name': 'download_project', 'args': [project['id']]}
                response = session.post(url, data=json.dumps(payload))
                try:
                    with open(fname, 'wb') as f:
                        f.write(response.content)
                except Exception as E:
                    print('WARNING, download succeed but write failed for project %s:\n%s' % (projectname, E.__repr__()))
                    failed.append(project['name'])
                    continue
            except Exception as E:
                print('WARNING, read succeeded but download failed for project %s:\n%s' % (projectname, E.__repr__()))
                failed.append(project['name'])
                continue
        except Exception as E:
            print('WARNING, read failed for project %s:\n%s' % (projectname, E.__repr__()))
            failed.append(projectname)
            continue
        success.append(fname)
        
    if len(success):
        print('The following projects were successfully downloaded:')
        for succ in success: print(succ)
    
    if len(failed):
        print('The following projects FAILED MISERABLY:')
        for fail in failed: print(fail)
    else:
        print('No projects failed downloading.')
    
    print('Done, at last.')
    
    try:    op.toc(T)
    except: print('Unable to calculate elapsed time, but it was probably a while.')




def backup():
    backupsfolder = 'backups'
    
    # Figure out last folder and current folder
    try:    
        mostrecent = sorted(os.listdir(backupsfolder))[-1]
    except:
        mostrecent = '0000-00-00'
        safemkdir(backupsfolder,mostrecent)
        try:    os.makedirs(os.path.join())
        except: pass

    now = datetime.datetime.now()
    current = '%4i-%02i-%02i' % (now.year, now.month, now.day)
    safemkdir(backupsfolder,current)
    
    
    # Download projects

    try:    password = sys.argv[1]
    except: password = None
    try:    savelocation = sys.argv[2]
    except: savelocation = None
    downloadprojects(password=password, savelocation=savelocation)
    
    return None


if __name__ == '__main__':
    backup()
