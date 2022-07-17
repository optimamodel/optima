# 1. Quick start guide

## 1.1. Introduction

Optima HIV is a software tool that assists national decision-makers and program managers in achieving maximum impact for every dollar invested in the HIV response. Optima HIV was developed by the Optima Consortium for Decision Science (www.ocds.co), in partnership with the World Bank.

This repository contains all the code required to run the Optima HIV software tool. For general information on Optima HIV, please see the User Guide (http://optimamodel.com/user-guide) For specific instructions on how to use the tool, please see the Reference Manual (http://optimamodel.com/manual).

If you have any questions, please email us at info@optimamodel.com.

## 1.2. Installation

This section describes the steps involved in installing and running Optima. Follow the instructions in this section.

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

That's it! **Unless you're a developer, you won't need to follow the rest of the instructions.**




# 2. Linux server setup

## 2.1. Backend installation

1. Install Anaconda Python 2.7

2. Clone Optima: `git clone https://github.com/optimamodel/optima.git`

3. Install Optima: `python setup.py develop`

4. Test that it works:
```
python
import optima as op
P = op.demo(doplot=False)
```

## 2.2. Database installation

1. Install additional Python packages: `pip install -r server/localrequirements.txt`

2. Install redis: `sudo apt-get install redis-server`

3. Install and set up postgres:
```
sudo apt install postgresql
sudo su postgres
createuser optima -P -s # password optima
createdb optima
```

4. Copy server settings: `cp server/config.example.py server/config.py`

## 2.3. Client installation

1. Install the packages:
```
sudo apt-get install npm
sudo apt-get install nodejs-legacy
```

2. Install npm and node packages:
```
sudo npm install -g bower # install globally, so need sudo
sudo npm install -g gulp
npm install
node node_modules/bower/bin/bower install
```

3. Build the client:
```
cd bin
./bulid_client.sh
```

## 2.4. Starting the service

1. Create the server service, e.g. `optimahiv.service`, in `/etc/systemd/system/`, modifying ports and folders as necessary:
```
[Unit]
Description=Optima HIV server
[Service]
ExecStart=/software/anaconda/bin/python -m server._twisted_wsgi 8080
Restart=always
User=optima
WorkingDirectory=/home/optima/tools/optima
[Install]
WantedBy=multi-user.target
```

2. Create the Celery service, e.g. `optimahivcelery.service`
```
[Unit]
Description=Optima HIV Celery
[Service]
ExecStart=/software/anaconda/bin/celery -A server.webapp.tasks.celery_instance worker -l info
Restart=always
User=optima
WorkingDirectory=/home/optima/tools/optima
```

3. Update the service monitor and start the services:
```
sudo systemctl daemon-reload
sudo service optimahiv start
sudo service optimahivcelery start
```

## 2.5 Testing and optional setup

1. Test by going to e.g. `hostname:8080`

2. To populate the demo projects, go to `hostname:8080/#/devregister` and create a user with username `_OptimaDemo` and password `_OptimaDemo`. Then run `python tests/makedemos.py`, and upload the two generated projects to this account.

3. That's all, folks!




# 3. Windows server setup

There are four steps to get full Optima set up:

1. The "backend" (the Optima Python package)

2. The "database" (postgres/redis)

3. The "client" (JavaScript/npm)

4. The "server" (Flask/Twisted)

## 3.1. Backend setup
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


## 3.2. Database setup
1. Download and install EDB Postgres version of PostgreSQL from (currently) https://www.enterprisedb.com/downloads/postgres-postgresql-downloads#windows  
(PostgreSQL is the database that stores all user and project data.) Postgres should automatically start as a service and be running (but you might need to reboot). You need to create a default postgres user with password e.g. `postgres`. You might need to add e.g. `C:\Program Files\PostgreSQL\9.6\bin` to the Windows PATH environment variable.

2. From the command prompt, enter:
```
createuser -P -s -U postgres optima # enter "optima" for the password
createdb -U optima optima
```
This creates a superuser named `optima`, and creates a database called `optima` accessible to this user. If you want to poke around your database, you can use pgAdmin from the Start menu.


## 3.3. Client setup
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


## 3.4. Server setup
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


## 3.5. Rebuilding client/restarting the server
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



# 4. Wisdom

This section contains random pieces of wisdom we have encountered along the way.

## 4.1 Workflows

- Make sure you pull and push from the repository regularly so you know what everyone else is doing, and everyone else knows what you're doing. If your branch is 378 commits behind develop, you're the sucker who's going to have to merge it.  

- There is very unclear advice about how to debug Python. It's actually fairly simple: if you run Python in interactive mode (e.g. via Spyder or via `python -i`), then if a script raises an exception, enter this in the console just after the crash:  
`import pdb; pdb.pm()`  
You will then be in a debugger right where the program crashed. Type `?` for available commands, but it works like how you would expect. Alternatively, if you want to effectively insert a breakpoint into your program, you can do this with  
`import pdb; pdb.set_trace()`  
No one knows what these mysterious commands do. Just use them.  

- For benchmarking/profiling, you can use `tests/benchmarkmodel.py`. It's a good idea to run this and see if your changes have slowed things down considerably. It shows how to use the line profiler; Spyder also comes with a good function-level (but not line) profiler.


## 4.2 Python gotchas

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

