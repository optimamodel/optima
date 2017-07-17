# Introduction to the Optima webserver

_ WARNING, much of this document is out-of-date! _

- the main webserver is `api.py`, a `python` application, written in the `flask` framework.
 `api.py` defines the way URL requests are converted into HTTP responses to the
  webclient, you can see a list of available API calls at <http://sandbox.optimamodel.com/api/spec.html#!/spec>,
  or locally, once the webserver is running <http://localhost:8080/api/spec.html>
- `flask` is a micro-framework to provide libraries to build `api.py`
- `api.py` stores projects in a `postgres` database, a robust high-performant database.
  It uses the `sqlalchemy` python library to interface with the database,
  the database schema, tables and entries. You can directly interrogate the `postgres`
  database using the standard `postgres` command-line tools, such as `psql`. The
  database schema is stored in `server/webapp/dbmodels.py`.
- `bin/run_server.py` uses `twisted` to bridge `api.py` to the outgoing port of your computer using the
  `wsgi` specification. `run_server.py` also serves the client js files from the `client` folder
- to carry out parallel simulations, `server/webapp/tasks.py` is a  `celery` daemon that listens for jobs
  from `api.py`, which is communicated through an in-memory/intermittent-disk-based `redis`
  database.

## To modify the database (not out of date!)

0. First, back up (may also need `-U optima` assuming SQL user `optima`; may be e.g. `postgres`):

  `pg_dump optima > optima_old_db.sql`

0. Log into the database:

  `psql optima`

0. Perform the required commands, e.g.:

  ```
  ALTER TABLE users
ADD COLUMN country character varying(60),
ADD COLUMN organization character varying(60),
ADD COLUMN position character varying(60);
```

0. Exit (e.g. `Ctrl+D`), and the database should be updated

## Installing the server

_On Mac_

1. install `brew` as it is the best package-manager for Mac OSX:
    - `ruby -e “$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)”`
2. install `python` and all the required third-party `python` modules:
    - `brew install python`
    - to make sure `python` can find the Optima `<root>` directory, in the top `<root>` folder, run:
        `python setup.py develop`
    - to load all the `python` modules needed (such as `celery`, `flask`, `twisted` etc), in the `<root>/server` folder, run:
        `pip install -r localrequirements`
3. install the ruby `lunchy` controller for MacOSX daemons
    - `brew install ruby`
    - `sudo gem install lunchy`
4. install the `redis` and `postgres` database daemons:
    - `brew install postgres redis`
    - launch them: `lunchy start redis postgres`

_On Ubuntu:_

1. `sudo apt-get install redis-server`

## Configuring the webserver

Next, we set up the databases, brokers, url's that `api.py` will we use. We do this through the `config.py` file in the `<root>/server` folder. Here's an example of a `config.py` file:

```
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://optima:optima@localhost:5432/optima'
SECRET_KEY = 'F12Zr47j\3yX R~X@H!jmM]Lwf/,?KT'
UPLOAD_FOLDER = '/tmp/uploads'
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
REDIS_URL = CELERY_BROKER_URL
MATPLOTLIB_BACKEND = "agg"
```

You can choose which ports to use, the name of the databases. Matplotlib is the key python library
that generates the graphs, it must be set to the "agg" backend, otherwise it can cause GUI crashes with
the windowing system of your computer.

The port that `api.py` is run on, is set in `<root>/server/_twisted_wsgi.py`, which by default is 8080.


## Running the webserver

If you haven't already launched `redis` and `postgres`, launch them:  

`lunchy start redis postgres`

Then, from the `<root>/bin` directory:

- launch the webserver `./start_server.sh`
- launch the parallel-processing daemon `./start_celery.sh`

__!__ Note: whenever you make a change that could affect a celery task, you need to restart it manually.


## Files

- `api.py` - the webserver
- `export.py` - command-line to extract saved projects from the postgres database
- `import.py` - command-line to push projects into the database
- `config.py` - the configuration of the postgres/redis databases and ports for the webserver
- `localrequirements.txt` - python modules to be installed
- `venvrequirements.txt` - another version of `localrequirements.txt` but for use with virtualenv

In `server/webapp`:

- `handlers.py` - the URL handlers are defined here. The handlers only deal with JSON-data structures,
  UIDs, and upload/download files
- `parse.py` - routines defined here parse all the PyOptima objects into JSON-data structures. This is
   to separate the parsing from storing/running PyOptima objects
- `dataio.py` - the routines defined here, take JSON-data structures and pass them to the database, and
  run the simulations. PyOptima objects are converted with calls to `parse.py`
- `dbconn.py` - this is a central place to store references to the postgres and redis database
- `dbmodels.py` - the adaptor to the Postgres database with objects that map onto the database tables
- `exceptions.py` - common exceptions stored here
- `plot.py` - some specialist graph-mangling routines to work with the mpld3 library that generates graphs
- `tasks.py` - this is a conceptually difficult file - it defines both the daemons
   and the tasks run by the daemon. This file is called by `api.py` as entry point to talk to `celery`,
   and is run separately as the `celery` task-manager daemon.

## API documentation

Once you have configured the `api.py` server, you can browse api endpoints at
 <http://localhost:8080/api/spec.html#!/spec> on your local machine,
 or <http://sandbox.optimamodel.com/api/spec.html#!/spec>

The webserver API reads PyOptima objects and converts it to JSON dictionary structures that can be read by the web-client

### PyOptima API

PyOptima does not provide any formal documentation. The following is a working model of the PyOptima python objects, dervied from debugging working examples of PyOptima. It is described in a quasi-YAML format

```yaml
Parameterset (Parset):
    self.name: string # "default"
    self.uid: uuid
    self.project: pointer ref to project
    self.created: Datetime
    self.modified: Datetime
    self.popkeys:
        - str or tuple of 2 str # 2-tupe is necessary as these are used as dictionary hashes
        - ...
    self.resultsref:
        None
         -or-
        - Result
        - ...
    self.progsetname: string
    self.budget: budget # Store the budget that generated the parset, if any
    self.pars:
        - <odict>
            label: string or None
            male: array(bool) # for all populations
            female: array(bool) # for all populations
            injects: array(bool) # for all populations
            seworker: array(bool) # for all populations
            popkeys: ? list of str
            # initialized by partype: "initprev", "popsize", "meta", "timepar", "no", "constant"
            initprev: ...
            popsize: ...
            <par_short>:
                Par
                    self.name: str
                    self.short: str
                    self.limits: (0, [1 -or- 'maxmeta', 'maxrate' or 'maxpopsize'])
                    self.by: "pop", "pship", "tot", "fpop", "mpop", "tot"
                    self.fittable: "pop", "exp", "no", "meta", "cascade", "constant"
                    self.auto: "init", "popsize", "force", "inhomo", "no", "other", "test", "treat", "cascade"
                    self.cascade: 0 or 1 or None
                    self.coverage: 0 or 1 or None
                    self.visible: 0 or 1 or None
                    self.proginteract: "random" or None
                  -or-
                TimePar
                    <same as Par>
                    self.t: odict or None ??
                    self.y: odict or None ??
                    self.m: float ??
                  -or-
                PopsizePar
                    <same as Par>
                    self.p: odict ??
                    self.m: float
                    self.start: int
                  -or-
                Constant
                    <same as Par>
                    self.y: odict ??
        - <odict>
        - ...

Program:
    self.short:  str
    self.name:  str
    self.uid:  uuid
    self.targetpars:
        - param: string
          pop: string or 2-tuple(string)
    self.targetpops:
        - string or tuple of 2 strings
    self.targetpartypes
    self.costcovfn:
        Costcov
            self.ccopars:
                <odict>
                    t: list of ints
                    unitcost: list of 2tuple(float)
                    saturation: list of 2tuple(float)
            self.interaction: "additive", "nested", "random"
    self.costcovdata:
        t: list of ints
        cost: list of [float or None]
        coverage: list of [float or None]
    self.category: "No Category", string
    self.criteria:
        hivstatus: 'allstates', -or- list of strings ['gt200'...]
        pregnant: boolean
    self.targetcomposition:

Programset (Progset):
    self.name: string
    self.uid: uuid
    self.default_interaction:  default_interaction ??
    self.programs:  odict() ??
    self.defaultbudget:  odict() ??
    self.created:  Datetime
    self.modified:  Datetime
    self.covout:
        <odict>
           - <target_par_short>:
                <pop_key>:
                    Covout
                        self.ccopars: <odict>
                            t: list of ints
                            intercept: list of 2tuple(float)
                            <program_name>: list([float, float])
                        self.interaction: "additive", "nested", "random"
           - ...

Parscen:
    self.name: str
    self.parsetname: str
    self.t: None
    self.active: boolean
    self.resultsref: None -or- string # name of Results or Multires
    self.scenparset: None -or- string
    self.pars
        - endval: float
          endyear: int
          name: string
          for: string -or- list of 1 string -or- tuple(string)
          startval: float
          startyear: int
        - ...

Budgetscen:
    self.name: string
    self.parsetname: string
    self.t: int -or- list of int
    self.active: boolean
    self.resultsref:  None -or- string # name of Results or Multires
    self.scenparset:  None -or- string
    self.progsetname: string
    self.budget:
        <program_short>: array(list of floats)
        ....

Coveragescen:
    self.name: string
    self.parsetname: string
    self.t: int -or- list of int
    self.active: boolean
    self.resultsref:  None -or- string # name of Results or Multires
    self.scenparset:  None -or- string
    self.progsetname: string
    self.coverage:
        <program_short>: array(list of floats)
        ....

Optimizations:
    self.name: string # "default"
    self.uid: uuid
    self.project: Project
    self.created: Datetime
    self.modified: Datetime
    self.parsetname: string
    self.progsetname: string
    self.resultsref:  None # Store pointer to results
    self.objectives:
       base:
       budget: int
       deathfrac: float
       deathweight: int
       end: int
       incifrac: float
       inciweight: int
       keylabels: ??
       keys: ??
       start: int
       which: "money" or "outcomes"
    self.constraints:
        max:
            <odict>
               - <program_short>: float
               - ...
        min:
            <odict>
               - <program_short>: float
               - ...
        name:
            <odict>
               - <program_short>: str
               - ...

Result:
    self.name: string # Name of this parameter
    self.isnumber:  isnumber # Whether or not the result is a number (instead of a percentage)
    self.pops:  pops # The model result by population, if available
    self.tot:  tot # The model result total, if available
    self.datapops:  datapops # The input data by population, if available
    ...?

Resultset:
    self.uid: uuid
    self.created: Datetime
    self.name: string
    ...?

Settings:
    self.dt: float # Timestep
    self.start: float # implied int, Default start year
    self.end: float # implied int # Default end year
    self.hivstates:  ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'lt50']
    self.healthstates:  ['susreg', 'progcirc', 'undx', 'dx', 'care', 'usvl', 'svl', 'lost', 'off']
    self.ncd4: int # number of hivstates
    self.nhealth: int # number of healthstates
    # Health states by diagnosis
    self.susreg  :  arange(0,1) # Regular uninfected, may be uncircumcised
    self.progcirc:  arange(1,2) # Uninfected, programatically circumcised
    self.undx    :  arange(0*self.ncd4+2, 1*self.ncd4+2) # Infected, undiagnosed
    self.dx      :  arange(1*self.ncd4+2, 2*self.ncd4+2) # Infected, diagnosed
    self.care    :  arange(2*self.ncd4+2, 3*self.ncd4+2) # Infected, in care
    self.usvl    :  arange(3*self.ncd4+2, 4*self.ncd4+2) # Infected, on treatment, with unsuppressed viral load
    self.svl     :  arange(4*self.ncd4+2, 5*self.ncd4+2) # Infected, on treatment, with suppressed viral load
    self.lost    :  arange(5*self.ncd4+2, 6*self.ncd4+2) # Infected, but lost to follow-up
    self.off     :  arange(6*self.ncd4+2, 7*self.ncd4+2) # Infected, previously on treatment, off ART, but still in care
    self.nsus    :  len(self.susreg) + len(self.progcirc)
    self.ninf    :  self.nhealth - self.nsus
    # Health states by CD4 count
    spacing:  arange(self.ninf)*self.ncd4
    self.acute:  2 + spacing
    self.gt500:  3 + spacing
    self.gt350:  4 + spacing
    self.gt200:  5 + spacing
    self.gt50 :  6 + spacing
    self.lt50 :  7 + spacing
    self.aidsind:  self.hivstates.index('gt50') # Find which state corresponds to AIDS...kind of ugly, I know
    # Combined states
    self.sus      :  cat([self.susreg, self.progcirc]) # All uninfected
    self.alldx    :  cat([self.dx, self.care, self.usvl, self.svl, self.lost, self.off]) # All people diagnosed
    self.allcare  :  cat([         self.care, self.usvl, self.svl,            self.off]) # All people in care
    self.alltx    :  cat([                    self.usvl, self.svl]) # All people on treatment
    self.allplhiv :  cat([self.undx, self.alldx]) # All PLHIV
    self.allstates:  cat([self.sus, self.allplhiv]) # All states
    self.nstates  :  len(self.allstates) # Total number of states
    self.statelabels: list of str # same number as self.healthstates
    # Non-cascade settings/states
    self.usecascade:  False # Whether or not to actually use the cascade
    self.tx :  self.svl # Infected, on treatment -- not used with the cascade
    # Other
    self.optimablue:  (0.16, 0.67, 0.94) # The color of Optima
    self.verbose:  verbose # Default verbosity for how much to print out -- see definitions in utils.py:printv()
    self.safetymargin:  0.5 # Do not move more than this fraction of people on a single timestep
    self.eps:  1e-3 # Must be small enough to be applied to prevalence, which might be ~0.1% or less

Project:
    self.uid: uuid
    self.created: Datetime
    self.modified: Datetime
    self.spreadsheetdate: 'Spreadsheet never loaded'
    self.spreadsheet: None # Binary version of the spreadsheet file
    self.version: string
    self.gitbranch: ?
    self.gitversion: ?
    self.filename: None or string
    self.name:  string
    self.settings:  Settings(verbose=verbose) # Global settings
    self.data:  {} # Data from the spreadsheet
    self.parsets:
      <odict>
        - <parset_name>: Parameterset
        - ...
    self.progsets:
      <odict>
         - <progset_name>: Programset
        - ...
    self.scens:
      <odict>
        - <progset_name>: Programset
        - ...
    self.optims:
      <odict>
        - <progset_name>: Programset
        - ...
    self.results:
      <odict>
        - <progset_name>: Programset
        - ...
```

### Webserver API structures

The API calls deal with an intermediate data structures which is JSON-compatible, in other words data-structrues that are used in PyOptima - such as odicts and numpy arrays - must be converted to lists, dictionaries, strings, booleans, null or float.

The current JSON representations of the PyOptima objects are:

```yaml
program:
    active: boolean
    name: string
    short: string
    category: "Prevention", "Care and treatemet", "Management and administration", ...
    criteria: string
    optimizable: boolean
    populations:
    	- string -or- [2 strings]
    	- ...
    targetpars:
    	- active: boolean
    	  param: string
    	  pops: [string -or- [list of 2 strings]]
	    - ...
    costcov:
    	- t: list of number
    	  cost: [number -or- null] # same length as t
    	  coverage: [number -or- null] # same length as t
    	- ...
    ccopars:
        - t: list of number
          saturation: list of 2 numbers
          unitcost: list of 2 numbers


# used in create new program modal
defaultPrograms: [program]

progset:
    id: uuid_string
    project_id: uuid_string
    name: string
    created: datetime_string
    updated: datetime_string
    programs: [program] # contains also default programs that are not active

# used in create new parameter scenario modal
ykeysByParsetId:
    <parsetId>:
        <parameterShortName>:
            - val: number
              label: string
            - ...

scenario:
    id: uuid_string
    progset_id: uuid_string -or- null # since parameter scenarios don't have progsets
    parset_id: uuid_string
    name: string
    active: boolean
    years: list of number
    scenario_type: "parameter", "coverage" or "budget"
    ---
    pars:
    	- name: string
    	  for: string -or- [1 string] -or- [2 strings]
    	  startyear: number
    	  endyear: number
    	  startval: number
    	  endval: number
    	- ...
     -or-
    budget:
    	- program: string
    	  values: [number -or- null] # same length as years
    	- ...
     -or-
    coverage:
    	- program: string
    	  values: [number -or- null] # same length as years
    	- ...

project:
    id: uuid_string
    name: string
    user_id: uuid_string
    dataStart: number
    dataEnd: number
    populations:
        - age_from: number
          age_to: number
          female: number
          male: number
          name: string
          short: string
        - ...
    nProgram: number
    creation_time: datetime_string
    updated_time: datetime_string
    data_upload_time: datetime_string
    has_data: boolean
    has_econ: boolean

# used to load/save program outcome functions
progsetEffect:
    parset: uuid_string
    parameters:
        - name: string
          pop: string -or- [list of 2 strings]
          years:
              - interact: "random", "nested", or "additive"
                intercept_lower: number
                intercept_upper: number
                year: number
                programs:
                    - intercept_lower: number -or- null
                      intercept_lower: number -or- null
                      name: string
                    - ...
              - ...
        - ...

# used for new calibration parameter sets
defaultParameters:
    - fittable: string
      name: string
      auto: string
      partype: string
      proginteract: string
      short: string
      coverage: boolean
      by: string
      pships: list of strings
    - ...

# used in new project modal
defaultPopulations:
    - short: string
      name: string
      male: boolean
      female: boolean
      age_from: number
      age_to: number
      injects: boolean
      sexworker: boolean
    - ...

optimizations:
    - constraints:
          max:
              <program_short>: float or null
              ...
          min:
              <program_short>: float or null
              ...
          name:
              <program_short>: float or null
              ...
      id: string
      name: string
      objectives:
          base: null
          budget: number
          deathfrac: number
          deathweight: number
          end: number
          incifrac: number
          inciweight: number
          keylabels:
              <key>: string
              ...
          keys: list of strings
          start: number
          which: "outcomes", "outcome" "money"
      parset_id: uuid_string
      progset_id: uuid_string
      which: "outcomes", "outcome" "money"
    - ...
```
