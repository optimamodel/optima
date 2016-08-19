

# Optima API DOC

in YAML-like format

## Back-End documentation

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
    self.short = str
    self.name = str
    self.uid = uuid
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
    self.default_interaction = default_interaction ??
    self.programs = odict() ?? 
    self.defaultbudget = odict() ??
    self.created = Datetime
    self.modified = Datetime
    self.covout: 
        <odict>
           - <target_par_short>:
                <pop_key>: 
                    Covout
                        self.ccopars:
                            t: list of ints
                            intercept: list of 2tuple(float)
                        self.interaction: "additive", "nested", "random"
           - ...

Parscen
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
  
Budgetscen
    self.name: string
    self.parsetname: string
    self.t: int -or- list of int
    self.active: boolean
    self.resultsref = None -or- string # name of Results or Multires
    self.scenparset = None -or- string
    self.progsetname: string
    self.budget:
        <program_short>: array(list of floats)
        ....

Coveragescen
    self.name: string
    self.parsetname: string
    self.t: int -or- list of int
    self.active: boolean
    self.resultsref = None -or- string # name of Results or Multires
    self.scenparset = None -or- string
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
    self.resultsref = None # Store pointer to results
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

Result
    self.name: string # Name of this parameter
    self.isnumber = isnumber # Whether or not the result is a number (instead of a percentage)
    self.pops = pops # The model result by population, if available
    self.tot = tot # The model result total, if available
    self.datapops = datapops # The input data by population, if available
    ...?
    
Resultset
    self.uid: uuid
    self.created: Datetime
    self.name: string
    ...?
    
Settings
    self.dt: float # Timestep
    self.start: float # implied int, Default start year
    self.end: float # implied int # Default end year
    self.hivstates = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'lt50']
    self.healthstates = ['susreg', 'progcirc', 'undx', 'dx', 'care', 'usvl', 'svl', 'lost', 'off']
    self.ncd4: int # number of hivstates
    self.nhealth: int # number of healthstates
    # Health states by diagnosis
    self.susreg   = arange(0,1) # Regular uninfected, may be uncircumcised
    self.progcirc = arange(1,2) # Uninfected, programatically circumcised
    self.undx     = arange(0*self.ncd4+2, 1*self.ncd4+2) # Infected, undiagnosed
    self.dx       = arange(1*self.ncd4+2, 2*self.ncd4+2) # Infected, diagnosed
    self.care     = arange(2*self.ncd4+2, 3*self.ncd4+2) # Infected, in care 
    self.usvl     = arange(3*self.ncd4+2, 4*self.ncd4+2) # Infected, on treatment, with unsuppressed viral load
    self.svl      = arange(4*self.ncd4+2, 5*self.ncd4+2) # Infected, on treatment, with suppressed viral load
    self.lost     = arange(5*self.ncd4+2, 6*self.ncd4+2) # Infected, but lost to follow-up
    self.off      = arange(6*self.ncd4+2, 7*self.ncd4+2) # Infected, previously on treatment, off ART, but still in care
    self.nsus     = len(self.susreg) + len(self.progcirc)
    self.ninf     = self.nhealth - self.nsus
    # Health states by CD4 count
    spacing = arange(self.ninf)*self.ncd4 
    self.acute = 2 + spacing
    self.gt500 = 3 + spacing
    self.gt350 = 4 + spacing
    self.gt200 = 5 + spacing
    self.gt50  = 6 + spacing
    self.lt50  = 7 + spacing
    self.aidsind = self.hivstates.index('gt50') # Find which state corresponds to AIDS...kind of ugly, I know
    # Combined states
    self.sus       = cat([self.susreg, self.progcirc]) # All uninfected
    self.alldx     = cat([self.dx, self.care, self.usvl, self.svl, self.lost, self.off]) # All people diagnosed
    self.allcare   = cat([         self.care, self.usvl, self.svl,            self.off]) # All people in care
    self.alltx     = cat([                    self.usvl, self.svl]) # All people on treatment
    self.allplhiv  = cat([self.undx, self.alldx]) # All PLHIV
    self.allstates = cat([self.sus, self.allplhiv]) # All states
    self.nstates   = len(self.allstates) # Total number of states
    self.statelabels: list of str # same number as self.healthstates
    # Non-cascade settings/states
    self.usecascade = False # Whether or not to actually use the cascade
    self.tx  = self.svl # Infected, on treatment -- not used with the cascade
    # Other
    self.optimablue = (0.16, 0.67, 0.94) # The color of Optima
    self.verbose = verbose # Default verbosity for how much to print out -- see definitions in utils.py:printv()
    self.safetymargin = 0.5 # Do not move more than this fraction of people on a single timestep
    self.eps = 1e-3 # Must be small enough to be applied to prevalence, which might be ~0.1% or less
    
Project
    self.uid: uuid
    self.created: Datetime
    self.modified: Datetime
    self.spreadsheetdate: 'Spreadsheet never loaded'
    self.spreadsheet: None # Binary version of the spreadsheet file
    self.version: string
    self.gitbranch: ?
    self.gitversion: ?
    self.filename: None or string
    self.name = string
    self.settings = Settings(verbose=verbose) # Global settings
    self.data = {} # Data from the spreadsheet
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


## Simultion workflows


## JSON delivery structures

Must be dictionaries (no odicts) or lists (no odicts or numpy arrays) of strings or floats

JSON has no integers. In the current SQL library, any such structures stored as JSON fields are returned with strings as unicode.

These structures are my cleanup of structures designed by SSQ. I've tried to match, where possible, the naming conventions of the optima objects.

At the moment, it's an awkward mixture of camelCase and snake_case. Eventually all should be camelCase to fit JSON naming conventions.

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

## Legacy DB interface

To avoid any extra migration steps, the legacy interfaces will not be touched during refactoring.

class UserDb(db.Model):
    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    username = db.Column(db.String(255))
    name = db.Column(db.String(60))
    email = db.Column(db.String(200))
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, server_default=text('FALSE'))
    projects = db.relationship('ProjectDb', backref='user', lazy='dynamic')


class ProjectDb(db.Model):
    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    name = db.Column(db.String(60))
    user_id = db.Column(UUID(True), db.ForeignKey('users.id'))
    datastart = db.Column(db.Integer)
    dataend = db.Column(db.Integer)
    populations = db.Column(JSON)
    created = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    version = db.Column(db.Text)
    settings = db.Column(db.LargeBinary)
    data = db.Column(db.LargeBinary)
    has_econ = db.Column(db.Boolean)
    blob = db.Column(db.LargeBinary)
    working_project = db.relationship('WorkingProjectDb', backref='related_project', uselist=False)
    project_data = db.relationship('ProjectDataDb', backref='project', uselist=False)
    project_econ = db.relationship('ProjectEconDb', backref='project', uselist=False)
    parsets = db.relationship('ParsetsDb', backref='project')
    results = db.relationship('ResultsDb', backref='project')
    progsets = db.relationship('ProgsetsDb', backref='project')
    scenarios = db.relationship('ScenariosDb', backref='project')
    optimizations = db.relationship('OptimizationsDb', backref='project')


class ParsetsDb(db.Model):
    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    name = db.Column(db.Text)
    created = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    pars = db.Column(db.LargeBinary)


class ResultsDb(db.Model):
    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    parset_id = db.Column(UUID(True), db.ForeignKey('parsets.id'))
    # When deleting a parset we only delete results of type CALIBRATION
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id', ondelete='SET NULL'))
    calculation_type = db.Column(db.Text)
    blob = db.Column(db.LargeBinary)


class WorkingProjectDb(db.Model):  # pylint: disable=R0903
    id = db.Column(UUID(True), db.ForeignKey('projects.id'), primary_key=True)
    is_working = db.Column(db.Boolean, unique=False, default=False)
    work_type = db.Column(db.String(32), default=None)
    project = db.Column(db.LargeBinary)
    parset_id = db.Column(UUID(True)) # not sure if we should make it foreign key here
    work_log_id = db.Column(UUID(True), default=None)


class WorkLogDb(db.Model):  # pylint: disable=R0903
    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    work_type = db.Column(db.String(32), default=None)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    parset_id = db.Column(UUID(True))
    result_id = db.Column(UUID(True), default=None)
    start_time = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    stop_time = db.Column(db.DateTime(timezone=True), default=None)
    status = db.Column(work_status, default='started')
    error = db.Column(db.Text, default=None)


class ProjectDataDb(db.Model):  # pylint: disable=R0903
    id = db.Column(UUID(True), db.ForeignKey('projects.id'), primary_key=True)
    meta = deferred(db.Column(db.LargeBinary))
    updated = db.Column(db.DateTime(timezone=True), server_default=text('now()'))


class ProjectEconDb(db.Model):  # pylint: disable=R0903
    id = db.Column(UUID(True), db.ForeignKey('projects.id'), primary_key=True)
    meta = deferred(db.Column(db.LargeBinary))
    updated = db.Column(db.DateTime(timezone=True), server_default=text('now()'))


class ProgramsDb(db.Model):
    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    progset_id = db.Column(UUID(True), db.ForeignKey('progsets.id'))
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    category = db.Column(db.String)
    name = db.Column(db.String)
    short = db.Column('short_name', db.String)
    pars = db.Column(JSON)
    active = db.Column(db.Boolean)
    targetpops = db.Column(ARRAY(db.String), default=[])
    criteria = db.Column(JSON)
    costcov = db.Column(JSON)
    ccopars = db.Column(JSON)
    created = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())


class ProgsetsDb(db.Model):
    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    name = db.Column(db.String)
    created = db.Column(db.DateTime(timezone=True), server_default=text('now()'))
    updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    programs = db.relationship('ProgramsDb', backref='progset', lazy='joined')
    effects = db.Column(JSON)


class ScenariosDb(db.Model):
    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id')) 
    name = db.Column(db.String)
    scenario_type = db.Column(db.String)
    active = db.Column(db.Boolean)
    progset_id = db.Column(UUID(True), db.ForeignKey('progsets.id')) # or None
    parset_id = db.Column(UUID(True), db.ForeignKey('parsets.id'))
    blob = db.Column(JSON)


class OptimizationsDb(db.Model):
    id = db.Column(UUID(True), server_default=text("uuid_generate_v1mc()"), primary_key=True)
    project_id = db.Column(UUID(True), db.ForeignKey('projects.id'))
    name = db.Column(db.String)
    which = db.Column(db.String)
    progset_id = db.Column(UUID(True), db.ForeignKey('progsets.id'))
    parset_id = db.Column(UUID(True), db.ForeignKey('parsets.id'))
    objectives = db.Column(JSON)
    constraints = db.Column(JSON)
