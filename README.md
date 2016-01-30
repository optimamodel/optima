1. Overview
========

This README describes the steps involved in installing Optima. For detailed usage instructions, please see other documentation, provided to users on request. Users/developers may also want to look at the final section of this document.

To use the Optima model from Python directly with the browser-based user interface, follow the instructions in "Optima model setup". Otherwise, follow all instructions.



2. Optima model setup
==============

2.1 Quick start installation
------------

To install, run `python setup.py develop` in the root repository directory. This will add Optima to the system path. Optima can then be used via Python. Note: do **not** use `python setup.py install`, as this will copy the source code into your system Python directory, and you won't be able to modify or update it easily. To uninstall, run `python setup.py develop --uninstall`.

2.2 Detailed instructions
---------

### 2.2.1 Preliminaries
0. Make sure you have a GitHub (http://github.com) account, plus either git or the GitHub app (http://desktop.github.com) -- which it looks like you do, if you're reading this :)
0. Clone the Optima repository: https://github.com/optimamodel/Optima.git
0. Make sure you have a version of scientific Python. Easiest to set up is probably Anaconda (https://store.continuum.io/cshop/anaconda/).

### 2.2.2 Dependencies
If you use Anaconda, everything should be taken care of, except possibly `pyqt4`, which is needed for the Python GUI.

If you don't want to use Anaconda, you'll need to install the dependencies yourself. If you install the latest versions of `numpy`, `matplotlib`, and `xlrd`, most of the backend should work. `mpld3` is required for viewing plots in the browser (not essential).

The full list of requirements (including for the frontend) is given in `server/requirements.txt`. However, note that `run.sh` will create a virtual environment with these packages even if you don't have them available on your system.

### 2.2.3 Python path
The last step is to make sure that Optima is available on the Python path. There are several ways of doing this:
 0. **Option 1: Spyder path**
    0. Run Spyder (part of Anaconda)
    0. Under the “Tools” (Linux and Windows) or “python” (under Mac) menu, go to “PYTHONPATH Manager”
    0. Select the Optima folder (e.g. `C:\Users\Alice\GitHub\Optima` on Windows) and click OK.
 0. **Option 2: modify system path**
    0. **Option 2A** (all operating systems): Go to the Optima root folder (in a terminal on Mac or Linux; in a command prompt [cmd.exe] in Windows) and run  
    `python setup.py develop`  
    Note: if Spyder does not use the system Python (which can happen in some cases), this will not work. In this case:
       0. Inside a Spyder console, type  
          `import sys; sys.executable`
       0. Replace the above command with the location of this executable, e.g.  
          `/software/anaconda/bin/python setup.py develop`
    0. **Option 2B** (Linux, Mac only): Add the Optima folder to `~/.bashrc` or `~/.bash_profile`, e.g.  
    `export PYTHONPATH=$PYTHONPATH:/users/alice/github/optima`  
    [NB: if you don't use `bash`, you are probably a hacker and don't need these instructions.]
    0. **Option 2C** (Windows only): search for “variables” from the Start Menu; the option should be called something like “Edit environment variables for your account”. Under “user variables”, you should see “PYTHONPATH” listed. Add the folder for the Optima repository, e.g.  
    `C:\Users\Alice\GitHub\Optima`  
    If there are already things on the Python path, add this to the end separated by a semicolon and no space, e.g.  
    `C:\Anaconda2\Library\bin;C:\Users\Alice\GitHub\Optima`

2.3 Verification/usage
-------
If you followed the steps correctly, you should be able to run  
`import optima`  
from a Python console (either the system console or the Spyder console)

For usage examples, see the scripts in the `tests` folder. In particular, `testworkflow.py` shows a typical usage example.





3. Database setup
=====

*For further details, see server/db/README.md*

For the development environment setup Optima needs to use a Postgres database created using:

- name: `optima`
- host: `localhost`
- port: `5432`
- username: `optima`
- password: `optima`

For example, use these commands (may need to run e.g. `sudo su postgres` first, but they are run from the shell, not from the `psql` console) *from the root Optima directory*:

```bash
createdb optima # Create Optima database -- for run.sh
createdb test # Create test database -- for test.sh
createuser optima -P -s # with password optima
createuser test -P -s # with password test
source server/p-env/bin/activate # ...not sure what this does
migrate version_control postgresql://optima:optima@localhost:5432/optima server/db/ # Allow version control
migrate upgrade postgresql://optima:optima@localhost:5432/optima server/db/ # Run the migrations to be safe
```






4. Client setup
===============

*For further details, see client/README.md*

This has been made using seed project [ng-seed](https://github.com/StarterSquad/ngseed/wiki)


4.1 Installing nginx
-------------------

0. Install nginx:
   - on Mac, use brew:  `brew install nginx`  
   - on Ubuntu:  `sudo apt-get install nginx`
  - on CentOS:  `sudo yum install nginx`
  - after install, run:  `sudo nginx`

0. Edit `client/nginx.conf.example`** and replace `ABSOLUTE_PATH_TO_PROJECT_SOURCE` with you local Optima path (you can even rename this to better name like `optima_nginx.conf`).

0. Enable the new configuration:
  - on Mac:
      - Copy the file created in step 2 to `/usr/local/etc/nginx/servers`, or  
      - Go to you local nginx configuration folder (usually: `/usr/local/etc/nginx`). And open `nginx.conf`, add a line there to include the nginx configuration file for Optima like:
      ```
      server {
        ...
        include {PATH_TO_CONFIG_FILE}/optima-nginx.conf;
      }
      ```
  - on Linux:
      - copy the file created in step 2 to `/etc/nginx/sites-enabled/` (or copy it to `/etc/nginx/sites-available/` and create a symlink to it from `/etc/nginx/sites-enabled/`)

0. *After any change to the configuration file*, restart `nginx`:
  - on Mac:  
      `sudo nginx -s stop`
      `sudo nginx`

  - on Linux:  
      `sudo service nginx restart`


  4.2 Installing the client
  ------------

      # Run script client/clean_build.sh.

        In case you face issue in executing ./clean_build.sh you can alternatively execute commands:
         1. npm install
         2. npm -g install bower (if you do not have bower already globally installed)
         3. npm -g install gulp (if you do not have gulp already globally installed)
         4. Create file client/source/js/version.js and add this content to it "define([], function () { return 'last_commit_short_hash'; });"
            (Where last_commit_short_hash is short hash for the last commit).





5. Server setup
===============

*For further details, see server/README.md*


5.1 Installation
------------

This component requires ([pip](http://pip.readthedocs.org/en/latest/installing.html)), [PostgreSQL](http://www.postgresql.org/download/) and [VirtualEnv](http://virtualenv.readthedocs.org/en/latest/).

Install virtual env:

`$ pip install virtualenv`


Copy the example config and configure it accordingly:

`$ cp src/config.example.py src/config.py`


Run the server:

`$ ./run.sh`

To use pre-installed system-wide python libraries, you can also run the server using:

 $ ./run.sh --system

ATTENTION: config.example.py (the reference config) can be changed (e.g. new settings added or old settings removed). If you have problems with running Optima locally, look at the reference config file and compare it with your version.


5.2 Tests
------------

Run the testsuite from your server directory:

    ./test.sh

In order to run a single test file and activate logging you can use:

    test.sh /src/tests/project_test.py

Same as with `run.sh`, you can use `--system` as first argument to `test.sh` in order to use pre-installed system-wide python libraries.

Make sure you have user "test" with the password "test" and database "optima_test" in order to run the tests using database.


6. Usage
=======

If all steps he been completed, run `run.sh` in the server directory, and then go to `http://optima.dev` in your browser (preferably Chrome). You should see the Optima login screen.

In order to use the application you need to login a registered user. In order to register a new user visit:  
`http://optima.dev/#/register`
and register using any details.

Happy Optimaing!

7. Wisdom
=========

This section contains random pieces of wisdom we have encountered along the way.

7.1 Workflows
------------
- Make sure you pull and push from the repository regularly so you know what everyone else is doing, and everyone else knows what you're doing. If your branch is 378 commits behind develop, you're the sucker who's going to have to merge it.
- There is very unclear advice about how to debug Python. It's actually fairly simple: if you run Python in interactive mode (e.g. via Spyder or via `python -i`), then if a script raises an exception, enter this in the console just after the crash:  
`import pdb; pdb.pm()`   
You will then be in a debugger right where the program crashed. Type `?` for available commands, but it works like how you would expect. Alternatively, if you want to effectively insert a breakpoint into your program, you can do this with  
`import pdb; pdb.set_trace()`  
No one knows what these mysterious commands do. Just use them.
- For benchmarking/profiling, you can use `tests/benchmarkmodel.py`. It's a good idea to run this and see if your changes have slowed things down considerably. It shows how to use the line profiler; Spyder also comes with a good function-level (but not line) profiler.


7.2 Python gotchas
-----------------
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
