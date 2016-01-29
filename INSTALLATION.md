
INSTALLATION NOTES FOR MAC
==========================

1. package installations
2. install postgres databases
5. install nginx webserver
3. install python webserver
4. install node.js based frontend builder
6. run locally with test projects


# 1. Package installations

Requirements:

- homebrew
- python (Anaconda https://store.continuum.io/cshop/anaconda/)
- node.js
- postgre
- nginx
- git
- github

The project is stored at a private Github repository: 

    https://github.com/optimamodel/Optima

Once registered, clone into your directory:

    git clone git@github.com:optimamodel/Optima.git


# 2. Install postgres database

Install with brew:

    brew install postgres

Then if the initial database has not been created, you should initialize postgres at the directory:

    initdb /usr/local/var/postgres -E utf8

Now you must start `postgres`. In the notes (), it's suggested that `lunchy` should be used to start-and-stop `postgres`. Install that:

    gem install lunchy
    lunchy start postgres

Then you must create the database for Optima:

    createdb optima

Then create a user for the python web-server to access the database with the password `optima`:

    createuser optima -P -w

For testing purposes (`server\test.sh`), you should create test database:

    createdb optima_test

Then create a user with a password `test`:

    creatuser test -P -w

You then need to install the `uuid-ossp` module with the postgres commandline:

    psql -d optima -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'

Now you can run the rest of the project. More information on the database at <https://github.com/optimamodel/Optima/blob/develop/server/db/README.md>

When done, spin down postgres:

    lunchy stop postgres


# 3. The Nginx webserver

The web-server used for Optima is Nginx.

    brew install nginx

By default, the nginx config from the homebrew package is located at 

    /usr/local/etc/nginx/nginx.conf

You should replace this with: 

    https://gist.github.com/RomeshA/378d50efcaaed50b90c7 

This file can also be found in:

    client/nginx.conf.example

You must make some changes to path names in `nginx.conf`:

1. change the paths on lines 30 and 98 (marked “CHANGE”) to your local Optima directories. 
2. change the first line to correspond to your username and group (or whatever user/group you want to run Optima as - this user must have read and execute permissions to both the Optima directory and to all of its parents).

To run nginx, make sure it has been stopped:

    sudo nginx -s stop

Then start it using:

    sudo nginx

Alternatively, if your config file is located in an other location, use

    sudo nginx -c <conf file>


# 4. Install the python webserver

For the python webserver, you will need:

- python
- pip, the python package manager
- virtualenv, the python virtual environment

Then go into the `server` directory.

To install all needed modules:

    pip install -r ./requirements.txt

Then run the server:

    python api.py

Alternatively, use the bash script to run the python in a virtualenv environment. This is somewhat fragile and includes a database migration.

    ./run.sh

This will install a whole lot of Python packages into the virtualenv container and start the backend server. If you go to http://localhost:5000 you should see ‘OK’. Simulation console output will be also be printed in this terminal (e.g. while running an optimization, there will be activity shown in this window)

More information <https://github.com/optimamodel/Optima/blob/develop/server/README.md>

To test python webserver and the `optima_test` database in  `postgres`, run:

    ./test.sh


# 5. Frontend builder

For this, you will need `node.js` and its package manager, `npm`.

    brew install node npm

Once node is installed, go into the `client` directory.

    npm install -g install bower gulp

This installs globally available node packages.

Then to install all packages and to compile the front-end:

    ./clean_build.sh

More information <https://github.com/optimamodel/Optima/blob/develop/client/README.md>


# 6. Run locally

So you've installed the postgres databases, nginx, python webserver and built the front-end. Then in the browser, go to

    http://localhost/#/register

A convenient script is provided to run nginx, postgres and the python webserver:

    ./boot_dev_env.sh

This can also be achieved by:

    lunchy start postgres
    sudo nginx
    cd server
    python api.py

Create an account (your email address needs a @ in it), then you should be good to go.

When you're down, you need to shutdown `postgres` and `nginx`.

For example sets, clone the Analyses repository

    https://github.com/optimamodel/analyses.git

Pick an Analyses script to start with -- for example, if you need to update the spreadsheet, the best is updatespreadsheet.py in the Ukraine folder (i.e. this).

Make a copy of this file in a folder reflecting the country you’re working on.

Download the JSON and spreadsheet files you want to work with.

Update the paths to reflect your system: i.e., add the path you cloned Optima into to the findoptima() function, and update the paths to the JSON and spreadsheet files, i.e. these lines would have to change:

    origfile = '/u/cliffk/unsw/countries/ukraine/ukraine-may27.json'
    spreadsheetfile = '/u/cliffk/unsw/countries/ukraine/ukraine-may27.xlsx'
    newfile = '/u/cliffk/unsw/countries/ukraine/ukraine-may27-fixed.json'

Run the file (either via Spyder or via 'python updatespreadsheet.py')

Reupload the updated JSON.

