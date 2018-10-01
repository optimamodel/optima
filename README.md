# 1. Quick start guide

## 1.1. Introduction

Optima HIV is a software tool that assists national decision-makers and program managers in achieving maximum impact for every dollar invested in the HIV response. Optima HIV was developed by the Optima Consortium for Decision Science (www.ocds.co), in partnership with the World Bank.

This repository contains all the code required to run the Optima HIV software tool. For general information on Optima HIV, please see the User Guide (http://optimamodel.com/user-guide) For specific instructions on how to use the tool, please see the Reference Manual (http://optimamodel.com/manual).

If you have any questions, please email us at info@optimamodel.com.

## 1.2. Installation

This section describes the steps involved in installing and running Optima. Follow the instructions in this section. **Unless you're a developer, you won't need to follow the rest of the instructions.**

1. Download and install Anaconda, using default options (https://store.continuum.io/cshop/anaconda/).  
 **Make sure you download Python 2.7, not 3.6.**

2. Sign up for an account on GitHub (http://github.com) with a free plan.

3. Download and install the GitHub app (http://desktop.github.com) on Windows or Mac, or `sudo apt-get install git` on Linux.

4. Go to the Optima GitHub page (http://github.com/optimamodel/optima) and click on "Clone or download", followed by "Open in desktop" (or copy the link and clone)

5. Finally, set up the Python path:  
  i. Run Spyder (part of Anaconda), e.g. from the Start menu  
  ii. Under the "Tools" (Linux and Windows) or "python" (under Mac) menu, go to "PYTHONPATH Manager"  
  iii. Select the Optima folder (e.g. `C:\Users\Alice\GitHub\Optima` on Windows) and click OK.  


6. To check that everything works:  
  i. Run Spyder (e.g. Anaconda -> Spyder from the Start Menu in Windows; Anaconda Launcher or `spyder` from the Terminal on Mac or Linux)  
  ii. In the Spyder editor (File -> Open), go to the `Optima/tests` folder and open `simple.py`  
  iii. Run (F5, or select "Run" from the "Run" menu)  
  iv. You should see a figure appear -- note that it might appear in the console (if you're using IPython) or in a separate window but minimized.  






# 2. Setting up Optima on Windows (for developers only)

There are four steps to get full Optima set up:

1. The "backend" (the Optima Python package)

2. The "database" (postgres/redis)

3. The "client" (JavaScript/npm)

4. The "server" (Flask/Twisted)

## 2.1. Backend setup
1. Download and install Anaconda, using default options (https://www.continuum.io/downloads).   
Make sure you download Python 2.7, not 3.6.

2. Sign up for an account on GitHub (http://github.com) with a free plan.

3. Download and install Git from https://git-scm.com/download/win. If desired, you can also download and install the GitHub app (http://desktop.github.com).

4. Go to the Optima GitHub page and clone the Optima repository.

5. Finally, to set the Python path, open a command prompt, and in the Optima folder (e.g. `C:\Users\Alice\GitHub\Optima` on Windows) type `python setup.py develop`.

6. To check that everything works:  
  i. Run Spyder (e.g. Anaconda -> Spyder from the Start Menu)  
  ii. Open a new Python console (Console -> Python console)  
  iii. Type `from optima import demo; demo()` and press enter.  
  iv. You should see a figure appear -- note that it might appear in the console (if you're using IPython) or in a separate window but minimized.  

7. To improve the plotting in Spyder (e.g. allow the use of `pygui()`), go to `Tools > Preferences > IPython Console > Graphics > Backend` and select "Automatic". This makes figures appear in new windows rather than in the console.


## 2.2. Database setup
1. Download and install EDB Postgres version of PostgreSQL from (currently) https://www.enterprisedb.com/downloads/postgres-postgresql-downloads#windows  
(PostgreSQL is the database that stores all user and project data.) Postgres should automatically start as a service and be running (but you might need to reboot). You need to create a default postgres user with password e.g. `postgres`. You might need to add e.g. `C:\Program Files\PostgreSQL\9.6\bin` to the Windows PATH environment variable.

2. From the command prompt, enter:
```
createuser -P -s -U postgres optima # enter "optima" for the password
createdb -U optima optima
```
This creates a superuser named `optima`, and creates a database called `optima` accessible to this user. If you want to poke around your database, you can use pgAdmin from the Start menu.


## 2.3. Client setup
1. Download and install Node.js for Windows (it should be automatically added to path):
https://nodejs.org/en/download/  
Node.js is used to manage the packages used for the JavaScript frontend.

2. In the `optima/client` folder, run:
```
npm install -g bower
npm install -g gulp
npm install
node node_modules\bower\bin\bower install
```
This installs all the JavaScript packages required by Optima.

3. In the `optima/client` folder, run:  
`node node_modules\gulp\bin\gulp.js`  
This compiles and builds the JavaScript client, ready to be served.


## 2.4. Server setup
1. Install the additional Python packages required with  
```
pip install flask-login flask-sqlalchemy flask-restful-swagger mpld3 celery==3.1.23 redis twisted validate-email
```
or
```
pip install -r server/localrequirements.txt
```
  These are the modules required by the Flask API, as well as for plotting (mpld3), the task manager (celery), the temporary database (redis, which talks to postgres), and the server (twisted, which is an equivalent of e.g. Apache).

2. Download and install Redis (from the MSI) from:  
https://github.com/MSOpenTech/redis/releases  
(You may need to reboot after this.)

3. Copy `optima/server/config.example.py` to `optima/server/config.py`. This contains the configuration settings so all the different databases and APIs point to each other.

4. In the root Optima folder, run  
`python bin/run_server.py 8080`  
This actually starts the server.

5. In a separate command window, in the root Optima folder, run  
`python -m celery -A server.webapp.tasks.celery_instance worker -l info`  
Note: this starts the task manager, and is only required for running automatic calibrations, optimizations, etc., so can be skipped if you just want to test the basic setup.

6. Optima should be up and running now. In your browser (it's strongly recommended to use an incognito window in Chrome), go to  
`localhost:8080/#/register`  
and create a user with username `_OptimaLite`, password `_OptimaLite`.  
**This account must exist for Optima to work.**

7. Once this account has been created, you can now log out (Account > Log out) and use Optima as normal (i.e., register a new account with whatever name you want, then log in using this new account).

8. To test the installation, either click on "Upload project from spreadsheet" and select `optima/tests/concentrated.xlsx`, or from a Python console, type  
`import optima as op; P = op.demo(0); P.save()`  
which creates a file in that directory called `demo.prj`. Then in the browser, click on "Upload project from file" and select the `demo.prj` file.


## 2.5. Rebuilding client/restarting the server
1. You will need three command prompts open, all in the `optima/bin` folder. In the first command window, run:  
`win_build.cmd`  
This recompiles the HTML/JavaScript client and copies it to the `client/build` folder, which is what's served.

2. In the second command window, run (NB, you don't have to wait for the first command to finish):  
`win_server.cmd`  
This starts the Twisted/Flask server.

3. In the third window, run:  
`win_celery.cmd`  
This starts the Celery task manager

4. Once all three have finished, you can to go to `localhost:8080` in your browser, and the latest version of Optima should be running. You can check by going to `Account > Help` (after logging in) and making sure that the version info shown matches what you get from `git log` in the Optima folder.




# 3. Setting up Optima on Mac/Linux

** WARNING, these instructions are partially deprecated! **

## 2.1 Quick start installation

To install, run `python setup.py develop` in the root repository directory. This will add Optima to the system path. Optima can then be used via Python.

To uninstall, run `python setup.py develop --uninstall`.

Note: do **not** use `python setup.py install`, as this will copy the source code into your system Python directory, and you won't be able to modify or update it easily.


## 2.2 Detailed instructions

### 2.2.1 Preliminaries

1. Make sure you have a GitHub (http://github.com) account, plus either git or the GitHub app (http://desktop.github.com) -- which it looks like you do, if you're reading this :)

2. Clone the Optima repository: https://github.com/optimamodel/Optima.git

3. Make sure you have a version of scientific Python. Easiest to set up is probably Anaconda (https://store.continuum.io/cshop/anaconda/).

### 2.2.2 Dependencies

If you use Anaconda, everything should be taken care of, except possibly `pyqt4`, which is needed for the Python GUI.

If you don't want to use Anaconda, you'll need to install the dependencies yourself (via e.g. `pip install`). If you install the latest versions of `numpy`, `matplotlib`, `xlrd`, and `xlsxwriter`, all of the backend should work. The full list of requirements (including for the frontend) is given in `server/requirements.txt`.

### 2.2.3 Python path

The last step is to make sure that Optima is available on the Python path. There are several ways of doing this:

 1. **Option 1: Spyder path**  
    i. Run Spyder (part of Anaconda)  
    ii. Under the “Tools” (Linux and Windows) or “python” (under Mac) menu, go to "PYTHONPATH Manager"  
    iii. Select the Optima folder (e.g. `C:\Users\Alice\GitHub\Optima` on Windows) and click OK.  

 2. **Option 2: modify system path**  
    i. **Option 2A** (all operating systems): Go to the Optima root folder (in a terminal on Mac or Linux; in a command prompt [cmd.exe] in Windows) and run  
    `python setup.py develop`  
    Note: if Spyder does not use the system Python (which can happen in some cases), this will not work. In this case:  
       a. Inside a Spyder console, type  
          `import sys; sys.executable`  
       b. Replace the above command with the location of this executable, e.g.  
          `/software/anaconda/bin/python setup.py develop`  
    ii. **Option 2B** (Linux, Mac only): Add the Optima folder to `~/.bashrc` or `~/.bash_profile`, e.g.  
    `export PYTHONPATH=$PYTHONPATH:/users/alice/github/optima`  
    [NB: if you don't use `bash`, you are probably a hacker and don't need these instructions.]  
    iii. **Option 2C** (Windows only): search for “variables” from the Start Menu; the option should be called something like “Edit environment variables for your account”. Under “user variables”, you should see “PYTHONPATH” listed. Add the folder for the Optima repository, e.g.  
    `C:\Users\Alice\GitHub\Optima`  
    If there are already things on the Python path, add this to the end separated by a semicolon and no space, e.g.  
    `C:\Anaconda2\Library\bin;C:\Users\Alice\GitHub\Optima`  

### 2.3 Verification/usage

If you followed the steps correctly, you should be able to run
`import optima`
from a Python console (either the system console or the Spyder console)

For usage examples, see the scripts in the `tests` folder. In particular, `testbest.py` shows a typical usage example.





# 3. Database setup

**NOTE: Steps from here onwards are only required for frontend development.**

*For further details, see server/db/README.md*

## 3.1 Installing PostgreSQL

### Linux

On Linux, use

    sudo apt-get install install postgres

The database will start automatically (I think).

### Mac

On mac, install the `postgres` software with:

    brew install postgres

Then you create the default database store:

    initdb /usr/local/var/postgres -E utf8

To run the `postgres` daemon in a terminal:

```bash
postgres -D /usr/local/var/postgresbrew
```

If you want to, you can run the `postgres` daemon with the Mac system daemon manager `launchctl`, or via the ruby wrapper for `lunchy`.

### Windows

On Windows, download and install from e.g. https://www.enterprisedb.com/downloads/postgres-postgresql-downloads#windows.


## 3.2 Setting up the Optima database

For the development environment setup Optima needs to use a Postgres database created using:

- name: `optima`
- host: `localhost`
- port: `5432`
- username: `optima`
- password: `optima`

Warning: the migrate scripts requires a user called `postgres`. This may not have been installed for you. One way to do this is to switch the user on your system `postgres` before building the database:

    sudo su postgres

Alternatively, you can create the `postgres` user directly:

    createuser postgres -s

You will first need to install the python database migration tools:

```bash
pip install sqlalchemy-migrate psycopg2
```

Then to create the optima database, use these commands *from the root Optima directory* as `migrate` needs to find the migration scripts:

```bash
createdb optima # Create Optima database -- for run.sh
#createdb test # Create test database -- for test.sh
createuser optima -P -s # with password optima
#createuser test -P -s # with password test
#migrate version_control postgresql://optima:optima@localhost:5432/optima server/db/ # Allow version control
#migrate upgrade postgresql://optima:optima@localhost:5432/optima server/db/ # Run the migrations to be safe
```

The scripts require that the `optima` user is a superuser. To check this:

```bash
psql -d optima -c "\du"
```

You should be able to see the users `optima` and `postgres`, and they are set to superusers. If not, to set `optima` to superuser:

```bash
psql -d optima -c "ALTER USER optima with SUPERUSER;"
```



# 4. Client setup

*For further details, see client/README.md*

This has been made using seed project [ng-seed](https://github.com/StarterSquad/ngseed/wiki)

## 4.1 Installing the client

Run script:

    client/clean_build.sh

In case you face issue in executing ./clean_build.sh you can alternatively execute commands:

1. `npm install`  
2. `npm -g install bower (if you do not have bower already globally installed)`  
3. `npm -g install gulp (if you do not have gulp already globally installed)`  
4. Create file `client/source/js/version.js` and add this content to it:  
        `define([], function () { return 'last_commit_short_hash'; });`  
    (Where last_commit_short_hash is short hash for the last commit).  



# 5. Server setup

*For further details, see server/README.md*


## 5.1 Installation

This component requires:

- [pip](http://pip.readthedocs.org/en/latest/installing.html) - python packaging manager
- [VirtualEnv](http://virtualenv.readthedocs.org/en/latest/) - python environment manager
- [tox](http://http://tox.readthedocs.org/) - virtualenv manager
- [PostgreSQL](http://www.postgresql.org/download/)  - relational database
- [Redis](http://redis.io/) - memory caching
- [Celery](http://redis.io/) - distributed task queue

To install the Redis server:

_On Linux_:

    sudo apt-get install redis-server

_On Mac_:

```
    brew install redis
    gem install lunchy # a convenient daemon utility script
    ln -sfv /usr/local/opt/redis/*.plist ~/Library/LaunchAgents
    lunchy start redis
```

Copy over the setup:

    cp server/config.py.example server/config.py

NOTE: config.example.py (the reference config) can be changed (e.g. new settings added or old settings removed). If you have problems with running Optima locally, look at the reference config file and compare it with your version.

Then to run the server, there are two options -- directly (self-managed environment like Anaconda) or through a virtualenv (if you are a developer).

_Using the scripts directly (e.g. prod/Anaconda)_:

Make sure you have the requirements:

    pip install -r server/requirements.txt

Then run the server in one terminal:

    python bin/run_server.py 8080 # to start on port 8080

...and celery in the other:

    celery -A server.webapp.tasks.celery_instance worker -l info


_Using Virtualenvs (e.g. for development)_:

Install ``virtualenv`` and ``tox``:

    pip install virtualenv tox

Run the server in two separate terminals. These scripts will start Python in a `virtualenv` isolated Python environments.
If you wish to use system installed packages, append `--sitepackages` and it will not reinstall things that are already installed in the Python site packages.
First in one terminal:

    tox -e celery

Then in the other terminal:

    tox -e runserver



## 5.2 Tests

Run the test suite from your server directory:

    ./test.sh

In order to run a single test file and activate logging you can use:

    test.sh /src/tests/project_test.py

You can use `--system` as first argument to `test.sh` in order to use pre-installed system-wide python libraries.

Make sure you have user "test" with the password "test" and database "optima_test" in order to run the tests using database.


# 6. Linux server setup

## 1. Backend installation

1. Install Anaconda Python 2.7

2. Clone Optima: `git clone https://github.com/optimamodel/optima.git`

3. Install Optima: `python setup.py develop`

4. Test that it works: `python; import optima as op; P = op.demo(doplot=False)`

## 2. Client installation

1. Install additional Python packages: `pip install -r server/localrequirements.txt`

2. Install postgres:
```
sudo apt-get install install postgresql
sudo su postgres
createuser optima -P -s # password optima
createdb optima
```

3. Install redis: `sudo apt-get install redis-server`

4. Copy server settings: `cp server/config.example.py server/config.py`


# 7. Usage

If all steps have been completed, run ``tox -e runserver`` in the server directory, and then go to `http://optima.dev:8080` in your browser (preferably Chrome). You should see the Optima login screen.

In order to use the application you need to login a registered user. In order to register a new user, visit <http://optima.dev:8080/#/register>, and register using any details.

Happy Optimaing!



# 8. Wisdom

This section contains random pieces of wisdom we have encountered along the way.

## 8.1 Workflows

- Make sure you pull and push from the repository regularly so you know what everyone else is doing, and everyone else knows what you're doing. If your branch is 378 commits behind develop, you're the sucker who's going to have to merge it.  

- There is very unclear advice about how to debug Python. It's actually fairly simple: if you run Python in interactive mode (e.g. via Spyder or via `python -i`), then if a script raises an exception, enter this in the console just after the crash:  
`import pdb; pdb.pm()`  
You will then be in a debugger right where the program crashed. Type `?` for available commands, but it works like how you would expect. Alternatively, if you want to effectively insert a breakpoint into your program, you can do this with  
`import pdb; pdb.set_trace()`  
No one knows what these mysterious commands do. Just use them.  

- For benchmarking/profiling, you can use `tests/benchmarkmodel.py`. It's a good idea to run this and see if your changes have slowed things down considerably. It shows how to use the line profiler; Spyder also comes with a good function-level (but not line) profiler.


## 8.2 Python gotchas

- Do not declare a mutable object in a function definition, e.g. this is bad:  
```
def myfunc(args=[]):
  print(args)
```  
The arguments only get initialized when the function is declared, so every time this function is used, there will be a single `args` object shared between all of them! Instead, do this:  
```
def myfunc(args=None):
  if args is None: args = []
  print(args)
```  

- It's dangerous to use `type()`; safer to use `isinstance()` (unless you _really_ mean `type()`). For example,  
`type(rand(1)[0])==float`  
is `False` because its type is `<type 'numpy.float64'>`; use `isinstance()` instead, e.g.   `isinstance(rand(1)[0], (int, float))`  
 will catch anything that looks like a number, which is usually what you _really_ want.  
