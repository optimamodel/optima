'''
This script downloads projects and does a backup.

To use, type

    crontab -e

and add a line like

    0 4 * * * /software/anaconda/bin/python /home/optima/bin/backup.py admin zzz "http://hiv.optimamodel.com"

This will run the backup script at 4am every morning (local time).

Note that crontab skips bashrc settings and only gets the pythonpath from site.py.
'''

# Import essential packages
try:
    import requests
    import sys
    import os
    import json
    from hashlib import sha224
    from pylab import argsort, rand
    import datetime
    import filecmp
except Exception as E:
    with open('/tmp/optima_backup_error.log','w') as f:
        errormsg = 'Essential import for Optima backup failed: %s' % E.__repr__()
        f.write(errormsg)

# Non-essential imports
try:    import optima as op
except: pass


def safemkdir(*args):
    ''' Skip exceptions and handle join() '''
    fullpath = os.path.abspath(os.path.join(*args))
    try:    os.makedirs(fullpath)
    except: pass
    return fullpath
    

def downloadprojects(username=None, password=None, savelocation=None, server=None, overwrite=None, withresults=None):
    '''
    A utility for downloading all projects from an Optima 2.0+ server for an admin account.

    Here's how to use it with the defaults for 'admin' at hiv.optimamodel.com, saving to folder optimaprojects:

         python downloadprojects.py <username> <password> <savelocation>

    Version: 2017may23
    '''
    
    # Define defaults
    if username is None:     username     = 'admin'
    if password is None:     password     = 'zzz'
    if savelocation is None: savelocation = 'optimaprojects'
    if server is None:       server       = 'http://localhost:8080'
    if overwrite is None:    overwrite    = False
    if withresults is None:  withresults  = False
    
    # Try timing
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
    sortedprojects = []
    for o in order:
        sortedusernames.append(usernames[o])
        sortedprojectnames.append(projectnames[o])
        sortedprojects.append(projects[o])
    
    print('Downloading all projects...')
    nprojects = len(sortedprojectnames)
    for i in range(nprojects):
        username = sortedusernames[i]
        projectname = sortedprojectnames[i]
        project = sortedprojects[i]
        try:
            print('  Downloading user "%s" project "%s" (%i/%i)' % (username, projectname, i+1, nprojects))
    
            dirname = os.path.join(savelocation, username)
            safemkdir(dirname)
    
            fname = os.path.join(dirname, projectname+'.prj')
            if os.path.exists(fname):
                if overwrite:  print('    Downloaded already, overwriting...')
                else:          fname += '.new' # Just keep appending till the cows come home
            try:
                url = server + '/api/download'
                if withresults: downloadfunc = 'download_project_with_result'
                else:           downloadfunc = 'download_project'
                payload = {'name': downloadfunc, 'args': [project['id']]}
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
        print('All projects successfully downloaded.')
    
    print('Done, at last.')
    try:    op.toc(T)
    except: print('Could not import Optima so elapsed time is not available')
    return None




def backup():
    '''
    Script for actually doing backups. Usage is usually via cron, but can do manually too. Just run
    
        python backup.py <username> <admin_password> <server>
    
    Default is
    
        python backup.py admin zzz "http://localhost:8080"
    
    Version: 2017may23
    '''
    
    print('Starting backup...')
    
    try:
        
        defaultfolder = 'optima_backups'
        dbg = []
        
        # Create the backups folder
        backupsfolder = safemkdir(os.path.expanduser("~"), defaultfolder)
        
        # Figure out last folder and current folder
        folderlist = sorted(os.listdir(backupsfolder)) # WARNING, assumes everything in here is a folder
        try:    last = folderlist[-1]
        except: last = '0000-00-00'
        lastabs = safemkdir(backupsfolder,last)
        now = datetime.datetime.now()
        current = '%4i-%02i-%02i' % (now.year, now.month, now.day)
        currabs = safemkdir(backupsfolder,current)
        logfilename = os.path.join('/tmp','optimabackupdebug_%s_%0.0f.log'%(current,1e6*rand())) # Set the log file name
        
        
        # Check things
        assert os.path.isdir(lastabs), '%s is not a folder, please move it!'
        if lastabs==currabs: # Make sure they're not the same
            last = folderlist[-2]
            lastabs = safemkdir(backupsfolder,last)
            assert os.path.isdir(lastabs), 'Previous folder is not right either, giving up'
        msg = 'Last folder found is %s' % lastabs; print(msg); dbg.append(msg)
        msg = 'Current folder is %s' % currabs; print(msg); dbg.append(msg)
        
        
        
        # Actually download projects
        try:    username    = sys.argv[1]
        except: username    = None
        try:    password    = sys.argv[2]
        except: password    = None
        try:    server      = sys.argv[3]
        except: server      = None
        try:    overwrite   = sys.argv[4]
        except: overwrite   = None
        try:    withresults = sys.argv[5]
        except: withresults = None
        print('Downloading projects into the current folder: username=%s, server=%s' % (username, server))
        downloadprojects(username=username, password=password, savelocation=currabs, server=server, overwrite=overwrite, withresults=withresults)
        
        # Create symlinks
        subfolders = os.listdir(currabs)
        for subfolder in subfolders:
            lastsub = os.path.join(lastabs,subfolder)
            currsub = os.path.join(currabs,subfolder)
            msg = '  Working on subfolder %s...' % currsub; print(msg); dbg.append(msg)
            if os.path.isdir(currsub):
                currprojs = os.listdir(currsub)
                for currproj in currprojs:
                    msg = '    Working on project %s...' % currproj; print(msg); dbg.append(msg)
                    lastprojabs = os.path.abspath(os.path.join(lastsub, currproj))
                    currprojabs = os.path.abspath(os.path.join(currsub, currproj))
                    if os.path.exists(lastprojabs):
                        if filecmp.cmp(lastprojabs,currprojabs):
                            msg = '      Symlinking %s' % currprojabs; print(msg); dbg.append(msg)
                            os.remove(currprojabs)
                            os.symlink(lastprojabs, currprojabs)
                        else:
                            msg = '      -->%s and %s do not match' % (lastprojabs,currprojabs); print(msg); dbg.append(msg)
                    else:
                        msg = '    -->Path %s does not exist' % lastprojabs; print(msg); dbg.append(msg)
        try:
            with open(logfilename,'w') as f:
                f.write('\n'.join(dbg))
        except:
            print('Backup worked, but writing to log file failed')
    
    except Exception as E:
        try:
            errormsg = 'Optima backup script failed: %s' % E.__repr__()
            print(errormsg)
            with open(logfilename,'w') as f:
                f.write(errormsg)
        except:
            print('Everything failed horribly')
    
    return None


if __name__ == '__main__':
    backup()
