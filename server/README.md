Installation
------------

This component requires ([pip](http://pip.readthedocs.org/en/latest/installing.html)), [PostgreSQL](http://www.postgresql.org/download/) and [VirtualEnv](http://virtualenv.readthedocs.org/en/latest/).

Install virtual env:

`$ pip install virtualenv`


Copy the example config and configure it accordingly:

`$ cp src/config.example.py src/config.py`


Run the server:

`$ ./run.sh`


ATTENTION: config.example.py (the reference config) can be changed (e.g. new settings added or old settings removed). If you have problems with running Optima locally, look at the reference config file and compare it with your version.

Database
________

### Postgres

- Postgres database (http://www.postgresql.org/)
- setting up create the database and users from the commandline:

```
    $ createdb optima
    $ createdb optima_test
    $ createuser optima -P -s
    // with password optima
    $ createuser test -P -s
    // with password test
```

Database migrations
___________________

  See db/README

Tests
------------

Run the testsuite from your server directory:

    ./test.sh

In order to run a single test file and activate logging you can use:

    test.sh /src/tests/project_test.py

Make sure you have user "test" with the password "test" and database "optima_test" in order to run the tests using database.

User API
------------

These APIs allow front-end to get current user or login a user.

* `/api/user/current`

  Returns `401 Unauthorized` if user is not logged in. Otherwise this JSON:

  `{
	email: "iwein@startersquad.com"
	name: "Iwein Fuld"
   }`

* `/api/user/create`

  Following data is posted when creating a new user:

  `{
	email: "iwein@startersquad.com"
	name: "Iwein Fuld"
	password: 'whatever'
   }`

  On success, user is sent back this JSON:

  `{
     "email": "iwein@startersquad.com",
     "name": "Iwein Fuld"
   }`

   On name already used, user is sent back this JSON:

   `{
 	 status: "Username in use"
    }`

* `/api/user/login`

  Following data is posted when doing login:

  `
	email: "iwein@startersquad.com"
	password: "whatever"
   `

  On successful login, user is redirected to the home page.

  On login error, a 401 Unauthorized response is returned.

* `/api/user/logout`

  User is logged out and redirected back to the login page.

Project API
------------

These APIs allow front-end to work with projects.

* `/api/project/info`

  Returns `401 Unauthorized` if user is not logged in. Otherwise this JSON:

  `{
	name: "Example",
	dataStart: 2000,
	dataEnd: 2015,
	projectionStartYear: 2010,
	projectionEndYear: 2030,
	programs:
	    [{"saturating": true, "short_name": "Condoms", "name": "Condom promotion and distribution"},
		 ...
		],
	populations:
		[{"name": "Female sex workers", "short_name": "FSW", "sexworker": true, "hetero": true, "injects": false, "client": false, "female": true, "homo": false, "male": false},
		 {"name": "Clients of sex workers", "short_name": "Clients", "sexworker": false, "hetero": true, "injects": false, "client": true, "female": false, "homo": false, "male": true},
		 {"name": "Men who have sex with men", "short_name": "MSM", "sexworker": false, "hetero": false, "injects": false, "client": false, "female": false, "homo": true, "male": true},
		 ...
		]
   }`

Python Linting
------------

We linting the python code with pylint. You can run it with:

    pylint src/optima

The configuration can be found in `pylintrc`.
