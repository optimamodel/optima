_doc_ = """

parse.py
========

Functions to convert/revert Optima objects into JSON-compatible data structures.

Nomenclature:
 - get_*_from_* to extract data structures
 - set_*_on_* to modify a PyOptima object with data structure

There should be no references to the database or web-handlers here.
"""


from functools import partial
from uuid import UUID
from collections import defaultdict
from pprint import pprint

from flask import current_app
from flask.ext.restful import fields, marshal

from numpy import nan

import optima as op
from optima import loadpartable, partable, Par
from optima.defaults import defaultprograms

from server.webapp.exceptions import ParsetDoesNotExist, ProgramDoesNotExist, ProgsetDoesNotExist
from server.webapp.utils import normalize_obj


# PROJECTS

def get_project_years(project):
    settings = project.settings
    return range(int(settings.start), int(settings.end) + 1)


ALL_POPULATIONS_SOURCE = """
Short name;Full name;Male;Female;AgeFrom;AgeTo;Injects;SexWorker
FSW;Female sex workers;0;1;15;49;0;1;
Clients;Clients of sex workers;1;0;15;49;0;1;
MSM;Men who have sex with men;1;0;15;49;0;1;
Transgender;Transgender individuals;0;0;15;49;0;1;
PWID;People who inject drugs;0;0;15;49;1;0;
Male PWID;Males who inject drugs;1;0;15;49;1;0;
Female PWID;Females who inject drugs;0;1;15;49;1;0;
Children;Children;0;0;2;15;0;0;
Infants;Infants;0;0;0;2;0;0;
Males;Other males;1;0;15;49;0;0;
Females;Other females;0;1;15;49;0;0;
Other males;Other males [enter age];1;0;0;0;0;0;
Other females;Other females [enter age];0;1;0;0;0;0;
"""

keys = "short name male female age_from age_to injects sexworker".split()


def get_default_populations():
    result = []
    lines = [l.strip() for l in ALL_POPULATIONS_SOURCE.split('\n')][2:-1]
    for line in lines:
        tokens = line.split(";")
        result.append(dict(zip(keys, tokens)))
    for piece in result:
        for key in ['age_from', 'age_to']:
            piece[key] = int(piece[key])
        for key in "male female injects sexworker".split():
            piece[key] = bool(int(piece[key]))
    return result


"""
PyOptima Population data['pop'] structure;
<odist>
 - short: ['FSW', 'Clients', 'MSM', 'PWID', 'M 15+', 'F 15+']
 - long: ['Female sex workers', 'Clients of sex workers', 'Men who have sex with men', 'People who inject drugs', 'Males 15+', 'Females 15+']
 - male: [0, 1, 1, 1, 1, 0]
 - female: [1, 0, 0, 0, 0, 1]
 - age: [[15, 49], [15, 49], [15, 49], [15, 49], [15, 49], [15, 49]]
 - injects: [0, 0, 0, 1, 0, 0]
 - sexworker: [1, 0, 0, 0, 0, 0]
"""


def get_populations_from_project(project):
    data_pops = normalize_obj(project.data.get("pops"))
    populations = []
    for i in range(len(data_pops['short'])):
        population = {
            'short': data_pops['short'][i],
            'name': data_pops['long'][i],
            'male': bool(data_pops['male'][i]),
            'female': bool(data_pops['female'][i]),
            'age_from': int(data_pops['age'][i][0]),
            'age_to': int(data_pops['age'][i][1]),
            'injects': bool(data_pops['injects'][i]),
            'sexworker': bool(data_pops['sexworker'][i]),
        }
        populations.append(population)
    return populations


def set_populations_on_project(project, populations):
    data_pops = op.odict()

    for key in ['short', 'long', 'male', 'female', 'age', 'injects', 'sexworker']:
        data_pops[key] = []

    for pop in populations:
        data_pops['short'].append(pop['short'])
        data_pops['long'].append(pop['name'])
        data_pops['male'].append(int(pop['male']))
        data_pops['female'].append(int(pop['female']))
        data_pops['age'].append((int(pop['age_from']), int(pop['age_to'])))
        data_pops['injects'].append(int(pop['injects']))
        data_pops['sexworker'].append(int(pop['sexworker']))

    if project.data.get("pops") != data_pops:
        # We need to delete the data here off the project?
        project.data = {}

    project.data["pops"] = data_pops

    project.data["npops"] = len(populations)


def set_project_summary_on_project(project, summary):

    set_populations_on_project(project, summary.get('populations', {}))
    project.name = summary["name"]

    if not project.settings:
        project.settings = op.Settings()

    project.settings.start = summary["dataStart"]
    project.settings.end = summary["dataEnd"]


def get_project_summary_from_project(project):
    years = project.data.get('years')
    if years:
        data_start = years[0]
        data_end = years[-1]
    else:
        data_start = project.settings.start
        data_end = project.settings.end

    n_program = 0
    for progsets in project.progsets.values():
        this_n_program = len(progsets.programs.values())
        if this_n_program > n_program:
            n_program = this_n_program

    project_summary = {
        'id': project.uid,
        'name': project.name,
        'dataStart': data_start,
        'dataEnd': data_end,
        'populations': get_populations_from_project(project),
        'nProgram': n_program,
        'creationTime': project.created,
        'updatedTime': project.modified,
        'dataUploadTime': project.spreadsheetdate,
        'hasData': project.data != {},
        'hasEcon': "econ" in project.data
    }
    return project_summary


parameter_fields = {
    'fittable': fields.String,
    'name': fields.String,
    'auto': fields.String,
    'partype': fields.String,
    'proginteract': fields.String,
    'short': fields.String,
    'coverage': fields.Boolean,
    'by': fields.String,
    'pships': fields.Raw,
}


def get_project_parameters(project):
    parset_list = project.parsets.values()
    default_pars = [par['short'] for par in loadpartable(partable)]
    parameters = []
    added_par_keys = set()
    for parset in parset_list:
        for par in parset.pars:
            for par_key in default_pars:
                if par_key not in added_par_keys \
                        and par_key in par \
                        and isinstance(par[par_key], Par) \
                        and par[par_key].visible == 1 \
                        and par[par_key].y.keys():
                    parameter = par[par_key].__dict__
                    parameter['pships'] = []
                    if par[par_key].by == 'pship':
                        parameter['pships'] = par[par_key].y.keys()
                    parameters.append(parameter)
                    added_par_keys.add(par_key)
    return marshal(parameters, parameter_fields)


# PARSETS

def get_parset_from_project(project, parset_id):
    if not isinstance(parset_id, UUID):
        parset_id = UUID(parset_id)
    for parset in project.parsets.values():
        if parset.uid == parset_id:
            return parset
    raise ParsetDoesNotExist(project_id=project.uid, id=parset_id)


def get_parset_summaries(project):
    parset_summaries = []

    for parset in project.parsets.values():

        parset_summaries.append({
            "id": parset.uid,
            "project_id": project.uid,
            "pars": parset.pars,
            "updated": parset.modified,
            "created": parset.created,
            "name": parset.name
        })

    return parset_summaries

'''
Parameters data structure:
    [
      {
        "value": 13044975.57899749,
        "type": "exp",
        "subkey": "Males 15-49",
        "key": "popsize",
        "label": "Population size -- Males 15-49"
      },
      {
        "value": 0.7,
        "type": "const",
        "subkey": null,
        "key": "recovgt350",
        "label": "Treatment recovery rate into CD4>350 (%/year)"
      },
    ]
'''

def get_parameters_from_parset(parset, ind=0):
    parameters = []
    for key, par in parset.pars[ind].items():
        if hasattr(par, 'fittable') and par.fittable != 'no':
            if par.fittable == 'meta':
                parameters.append({
                    "key": key,
                    "subkey": None,
                    "type": par.fittable,
                    "value": par.m,
                    "label": '%s -- meta' % par.name,
                })
            elif par.fittable == 'const':
                parameters.append({
                    "key": key,
                    "subkey": None,
                    "type": par.fittable,
                    "value": par.y,
                    "label": par.name,
                })
            elif par.fittable in ['pop', 'pship']:
                for subkey in par.y.keys():
                    parameters.append({
                        "key": key,
                        "subkey": subkey,
                        "type": par.fittable,
                        "value": par.y[subkey],
                        "label": '%s -- %s' % (par.name, str(subkey)),
                    })
            elif par.fittable == 'exp':
                for subkey in par.p.keys():
                    parameters.append({
                        "key": key,
                        "subkey": subkey,
                        "type": par.fittable,
                        "value": par.p[subkey][0],
                        "label": '%s -- %s' % (par.name, str(subkey)),
                    })
            else:
                print('>> Parameter type "%s" not implemented!' % par.fittable)
    return parameters


def set_parameters_on_parset(parameters, parset, i_set=0):
    pars = parset.pars[i_set]
    for p_dict in parameters:
        key = p_dict['key']
        value = p_dict['value']
        subkey = p_dict['subkey']
        par_type = p_dict['type']
        value = float(value)
        if par_type == 'meta':  # Metaparameters
            pars[key].m = value
        elif par_type in ['pop', 'pship']:  # Populations or partnerships
            pars[key].y[subkey] = value
        elif par_type == 'exp':  # Population growth
            pars[key].p[subkey][0] = value
        elif par_type == 'const':
            pars[key].y = value
        else:
            print('>> Parameter type "%s" not implemented!' % par_type)


def print_parset(parset):
    result = {
        'popkeys': normalize_obj(parset.popkeys),
        'uid': str(parset.uid),
        'name': parset.name,
        'project_id': parset.project.id if parset.project else '',
    }
    s = pprint.pformat(result, indent=1) + "\n"
    for pars in parset.pars:
        for key, par in pars.items():
            if hasattr(par, 'y'):
                par = normalize_obj(par.y)
            elif hasattr(par, 'p'):
                par = normalize_obj(par.p)
            else:
                par = normalize_obj(par)
            s += pprint.pformat({key: par}) + "\n"
    return s


# PROGRAMS

def get_target_popsizes(project, parset, progset, program):
    years = get_project_years(project)
    popsizes = program.gettargetpopsize(t=years, parset=parset)
    return normalize_obj(dict(zip(years, popsizes)))


def parse_targetpars(targetpars):
    parameters = defaultdict(list)
    for parameter in targetpars:
        short = parameter['param']
        pop = parameter['pop']
        parameters[short].append(pop)
    pars = []
    for short, pop in parameters.items():
        pars.append({
            'active': True,
            'param': short,
            'pops': pop,
        })
    return pars


def make_pop_tuple(pop):
    return str(pop) if type(pop) in (str, unicode) else tuple(map(str, pop))


def revert_targetpars(pars):
    if pars is None:
        return []
    targetpars = []
    for par in normalize_obj(pars):
        if par.get('active', False):
            for pop in par['pops']:
                targetpars.append({
                    'param': par['param'],
                    'pop': make_pop_tuple(pop)
                })
    return targetpars


def parse_costcovdata(costcovdata):
    if costcovdata is None:
        return None
    result = []
    costcovdata = normalize_obj(costcovdata)
    n_year = len(costcovdata['t'])
    for i_year in range(n_year):
        entry = {
            'year': costcovdata['t'][i_year],
            'cost': costcovdata['cost'][i_year],
            'coverage': costcovdata['coverage'][i_year]
        }
        if entry["cost"] is None and entry["coverage"] is None:
            continue
        result.append(entry)
    return result


pluck = lambda l, k: [e[k] for e in l]
to_nan = lambda v: v if v is not None and v != "" else nan


def revert_costcovdata(costcov):
    result = {}
    if costcov:
        costcov = normalize_obj(costcov)
        result = {
            't': map(to_nan, pluck(costcov, 'year')),
            'cost': map(to_nan, pluck(costcov, 'cost')),
            'coverage': map(to_nan, pluck(costcov, 'coverage')),
        }
    return result


def revert_ccopars(ccopars):
    result = None
    if ccopars:
        result = op.odict({
            't': ccopars['t'],
            'saturation': map(tuple, ccopars['saturation']),
            'unitcost': map(tuple, ccopars['unitcost'])
        })
    return result


def parse_program_summary(program, progset, active):
    result = {
        'id': program.uid,
        'progset_id': progset.uid if progset else None,
        'active': active,
        'name': program.name,
        'short': program.short,
        'populations': normalize_obj(program.targetpops),
        'criteria': program.criteria,
        'targetpars': parse_targetpars(program.targetpars),
        'ccopars': normalize_obj(program.costcovfn.ccopars),
        'category': program.category,
        'costcov': parse_costcovdata(program.costcovdata),
        'optimizable': program.optimizable()
    }
    return result


def parse_default_program_summaries(project):
    return [parse_program_summary(p, None, False) for p in defaultprograms(project)]


# PROGSET OUTCOMES

'''
Progset outcome data structure:
    [ { 'name': 'numcirc',
        'pop': 'tot',
        'years': [ { 'interact': 'random',
                     'intercept_lower': 0.0,
                     'intercept_upper': 0.0,
                     'programs': [ { 'intercept_lower': None,
                                     'intercept_upper': None,
                                     'name': u'VMMC'}],
                     'year': 2016.0}]},
      { 'name': u'condcom',
        'pop': (u'Clients', u'FSW'),
        'years': [ { 'interact': 'random',
                     'intercept_lower': 0.3,
                     'intercept_upper': 0.6,
                     'programs': [ { 'intercept_lower': 0.9,
                                     'intercept_upper': 0.95,
                                     'name': u'FSW programs'}],
                     'year': 2016.0}]},
    ]
'''

def parse_outcomes_from_progset(progset):
    outcomes = []
    for par_short in progset.targetpartypes:
        pop_keys = progset.progs_by_targetpar(par_short).keys()
        for pop_key in pop_keys:
            covout = progset.covout[par_short][pop_key]
            n_year = len(covout.ccopars['t'])
            outcome = {
                'name': par_short,
                'pop': pop_key,
                'years': [
                    {
                        'intercept_upper': covout.ccopars['intercept'][i_year][1],
                        'intercept_lower': covout.ccopars['intercept'][i_year][0],
                        'interact': covout.ccopars['interact'][i_year]
                        if 'interact' in covout.ccopars.keys()
                        else 'random',
                        'programs': [
                            {
                                'name': program_name,
                                'intercept_lower': program_intercepts[i_year][0] if len(
                                    program_intercepts) > i_year else None,
                                'intercept_upper': program_intercepts[i_year][1] if len(
                                    program_intercepts) > i_year else None,
                            }
                            for program_name, program_intercepts in covout.ccopars.items()
                            if program_name not in ['intercept', 't', 'interact']
                            ],
                        'year': covout.ccopars['t'][i_year]
                    }
                    for i_year in range(n_year)
                    ]
            }
            outcomes.append(outcome)
    return outcomes


def put_outcomes_into_progset(outcomes, progset):
    for outcome in outcomes:
        for year in outcome['years']:
            par_short = outcome['name']
            if par_short not in progset.covout:
                continue
            covout = progset.covout[par_short]

            ccopar = {
                'intercept': (year['intercept_lower'], year['intercept_upper']),
                't': int(year['year']),
                'interact': year['interact'],
            }

            for program in year["programs"]:
                if program['intercept_lower'] is not None \
                        and program['intercept_upper'] is not None:
                    ccopar[program['name']] = \
                        (program['intercept_lower'], program['intercept_upper'])
                else:
                    ccopar[program['name']] = None

            islist = isinstance(outcome['pop'], list)
            poptuple = tuple(outcome['pop']) if islist else outcome['pop']
            if poptuple in covout:
                covout[poptuple].addccopar(ccopar, overwrite=True)


# PROGETS


def get_progset_summary(project, progset_name):
    """

    @TODO: targetpartypes and readytooptimize fields needs to be made consistent within ProgsetDb

    """

    progset = project.progsets[progset_name]

    active_programs = map(partial(parse_program_summary, progset=progset, active=True), progset.programs.values()),
    inactive_programs_odict = getattr(progset, "inactive_programs", {})
    inactive_programs = map(partial(parse_program_summary, progset=progset, active=False), inactive_programs_odict.values()),
    programs = list(active_programs[0]) + list(inactive_programs[0])

    default_programs = parse_default_program_summaries(project)

    # Overwrite with default name and category if applicable
    loaded_program_shorts = []
    default_program_by_short = {p['short']: p for p in default_programs}
    for program in programs:
        short = program['short']
        if short in default_program_by_short:
            default_program = default_program_by_short[short]
            if not program['name']:
                program['name'] = default_program['name']
            program['category'] = default_program['category']
        loaded_program_shorts.append(short)

    # append any default programs as inactive if not already in project
    for program in default_programs:
        if program['short'] not in loaded_program_shorts:
            programs.append(program)

    for program in programs:
        if program['category'] == 'No category':
            program['category'] = 'Other'

    progset_summary = {
        'id': progset.uid,
        'name': progset.name,
        'created': progset.created,
        'updated': progset.modified,
        'programs': programs,
        #'targetpartypes': progset_record.targetpartypes,
        #'readytooptimize': progset_record.readytooptimize
    }
    return progset_summary


def get_progset_summaries(project):
    progset_summaries = [
        get_progset_summary(project, name) for name in project.progsets]
    return {'progsets': normalize_obj(progset_summaries)}


def get_program_from_progset(progset, program_id, include_inactive=False):

    if not isinstance(program_id, UUID):
        program_id = UUID(program_id)

    if include_inactive:
        progset_programs = {}
        progset_programs.update(progset.programs)
        progset_programs.update(progset.inactive_programs)
    else:
        progset_programs = progset.programs

    programs = [
        progset_programs[key]
        for key in progset_programs
        if progset_programs[key].uid == program_id
    ]
    if not programs:
        raise ProgramDoesNotExist(id=program_id)
    return programs[0]


def get_progset_from_project(project, progset_id):
    if not isinstance(progset_id, UUID):
        progset_id = UUID(progset_id)

    progsets = [
        project.progsets[key]
        for key in project.progsets
        if project.progsets[key].uid == progset_id
    ]
    if not progsets:
        raise ProgsetDoesNotExist(project_id=project.uid, id=progset_id)
    return progsets[0]


def set_program_summary_on_progset(progset, summary):

    try:
        program = get_program_from_progset(progset, summary["id"], include_inactive=True)

        # It exists, so remove it first...
        try:
            progset.programs.pop(program.short)
        except KeyError:
            progset.inactive_programs.pop(program.short)

        program_id = program.uid
    except ProgramDoesNotExist:
        program_id = None
        pass

    program = op.Program(
        short=summary["short"],
        name=summary["name"],
        category=summary["category"],
        targetpars=revert_targetpars(summary["targetpars"]),
        targetpops=summary["populations"],
        criteria=summary["criteria"],
        ccopars=revert_ccopars(summary["ccopars"]),
        costcovdata=revert_costcovdata(summary["costcov"]))

    if program_id:
        program.uid = program_id

    if summary["active"]:
        progset.addprograms(program)
    else:
        progset.inactive_programs[program.short] = program

    progset.updateprogset()


def set_progset_summaries_on_project(project, progset_summaries, progset_id=None):
    """

    """
    progset_name = progset_summaries['name']
    progset_programs = progset_summaries['programs']

    if progset_name not in project.progsets:
        if progset_id:
            # It may have changed, so try getting via ID if we have it...
            progset = get_progset_from_project(project, progset_id)
            project.progsets.pop(progset.name)

            # Update the name and its reflection in the project.
            progset.name = progset_name
            project.progsets[progset_name] = progset
        else:
            # Probably a new one.
            project.progsets[progset_name] = op.Programset(name=progset_name)
    progset = project.progsets[progset_name]

    # Clear the current programs...
    progset.programs = op.odict()
    progset.inactive_programs = op.odict()

    for p in progset_programs:
        set_program_summary_on_progset(progset, p)

    progset.updateprogset()

    current_app.logger.debug("!!! name and programs data : %s, \n\t %s "%(progset_name, progset_programs))


def parse_parameters_from_progset_parset(settings, progset, parset):
    print ">> Parsing parameters"

    def convert(limit):
        return settings.convertlimits(limits=limit) if isinstance(limit, str) else limit

    def get_limits(par):
        result = map(convert, par.limits)
        return result

    target_par_shorts = set([p['param'] for p in progset.targetpars])
    pars = parset.pars[0]
    parameters = [
        {
            'short': par_short,
            'name': pars[par_short].name,
            'coverage': pars[par_short].coverage,
            'limits': get_limits(pars[par_short]),
            'interact': pars[par_short].proginteract,
            'populations': [
                {
                    'pop': popKey,
                    'programs': [
                        {
                            'name': program.name,
                            'short': program.short,
                        }
                        for program in programs
                        ]
                }
                for popKey, programs in progset.progs_by_targetpar(par_short).items()
                ],
        }
        for par_short in target_par_shorts
        ]

    return parameters


# SCENARIOS

'''
Data structure of a scenario_summary:
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
'''


def force_tuple_list(item):
    if isinstance(item, str) or isinstance(item, unicode):
        return [str(item)]
    if isinstance(item, list):
        if len(item) == 1:
            # this is for the weird case of ['tot']
            return str(item[0])
        return [tuple(map(str, tokens)) for tokens in item]
    else:
        return item


def convert_pars_list(pars):
    result = []
    for par in pars:
        result.append({
            'name': par['name'],
            'startyear': par['startyear'],
            'endval': par['endval'],
            'endyear': par['endyear'],
            'startval': par['startval'],
            'for': force_tuple_list(par['for'])
        })
    return result


def revert_pars_list(pars):
    result = []
    for par in pars:
        result.append({
            'name': par['name'],
            'startyear': par['startyear'],
            'endval': par['endval'],
            'endyear': par['endyear'],
            'startval': par['startval'],
            'for': par['for'][0] if len(par['for']) == 1 else par['for']
        })
    return result


def get_parameters_for_scenarios(project):
    """
    Returns parameters that can be modified in a scenario:
        <parsetID>:
            <parameterShort>:
                - val: number
                - label: string
    """
    parsets = {key: value for key, value in project.parsets.items()}
    y_keys = {
        str(parset.uid): {
            par.short: [
                {
                    'val': k,
                    'label': ' - '.join(k) if isinstance(k, tuple) else k
                }
                for k in par.y.keys()
            ]
            for par in parset.pars[0].values()
            if hasattr(par, 'y') and par.visible
        }
        for id, parset in parsets.iteritems()
    }
    return y_keys


def get_scenario_summary(project, scenario):
    """
    Returns scenario_summary as defined above
    """
    extra_data = {}

    # budget, coverage, parameter, any others?
    if isinstance(scenario, op.Parscen):
        scenario_type = "parameter"
        extra_data["pars"] = revert_pars_list(scenario.pars)
    elif isinstance(scenario, op.Coveragescen):
        scenario_type = "coverage"
        extra_data["coverage"] = scenario.coverage
    elif isinstance(scenario, op.Budgetscen):
        scenario_type = "budget"
        extra_data["budget"] = [{"program": x, "values": y} for x, y in scenario.budget.iteritems()]

    if hasattr(scenario, "progsetname"):
        progset_id = project.progsets[scenario.progsetname].uid
    else:
        progset_id = None

    if hasattr(scenario, "uid"):
        scenario_id = scenario.uid
    elif hasattr(scenario, "uuid"):
        scenario_id = scenario.uuid
    else:
        scenario_id = op.uuid()

    result = {
        'id': scenario_id,
        'progset_id': progset_id, # could be None if parameter scenario
        'scenario_type': scenario_type,
        'active': scenario.active,
        'name': scenario.name,
        'years': scenario.t,
        'parset_id': project.parsets[scenario.parsetname].uid,
    }
    result.update(extra_data)
    return result


def get_scenario_summaries(project):
    scenario_summaries = map(partial(get_scenario_summary, project), project.scens.values())
    return normalize_obj(scenario_summaries)


def set_scenario_summaries_on_project(project, scenario_summaries):
    # delete any records with id's that aren't in summaries

    project.scens = op.odict()

    for s in scenario_summaries:

        if s["parset_id"]:
            parset_name = get_parset_from_project(project, s["parset_id"]).name
        else:
            parset_name = False

        kwargs = {
            "name": s["name"],
            "active": s["active"],
            "parsetname": parset_name,
            "t": s.get("years"),

        }

        if "progset_id" in s and s["progset_id"]:
            progset_name = get_progset_from_project(project, s["progset_id"]).name

        if s["scenario_type"] == "parameter":
            scen = op.Parscen(
                pars=convert_pars_list(s["pars"]),
                **kwargs)

        elif s["scenario_type"] == "coverage":
            scen = op.Coveragescen(
                coverage=s["coverage"],
                progsetname=progset_name,
                **kwargs)
        elif s["scenario_type"] == "budget":
            budget = op.odict({x["program"]:x["values"] for x in s["budget"]})

            scen = op.Budgetscen(
                budget=budget,
                progsetname=progset_name,
                **kwargs)

        if s.get("id"):
            scen.uid = UUID(s["id"])

        project.scens[scen.name] = scen



# OPTIMIZATIONS

'''
Optimization summary data structure:

{'constraints': {'max': {'ART': None,
                         'Condoms': None,
                         'FSW programs': None,
                         'HTC': None,
                         'Other': 1},
                 'min': {'ART': 1,
                         'Condoms': 0,
                         'FSW programs': 0,
                         'HTC': 0,
                         'Other': 1},
                 'name': {'ART': 'Antiretroviral therapy',
                          'Condoms': 'Condom promotion and distribution',
                          'FSW programs': 'Programs for female sex workers and clients',
                          'HTC': 'HIV testing and counseling',
                          'Other': 'Other'}},
 'name': 'Optimization 1',
 'objectives': {'base': None,
                'budget': 60500000,
                'deathfrac': None,
                'deathweight': 5,
                'end': 2030,
                'incifrac': None,
                'inciweight': 1,
                'keylabels': {'death': 'Deaths', 'inci': 'New infections'},
                'keys': ['death', 'inci'],
                'start': 2017,
                'which': 'outcomes'},
 'parset_id': 'af6847d6-466b-4fc7-9e41-1347c053a0c2',
 'progset_id': 'cfa49dcc-2b8b-11e6-8a08-57d606501764',
 'which': 'outcomes'}
 '''


def get_default_optimization_summaries(project):
    defaults_by_progset_id = {}
    for progset in project.progsets.values():
        progset_id = progset.uid
        default = {
            'constraints': op.defaultconstraints(project=project, progset=progset),
            'objectives': {}
        }
        for which in ['outcomes', 'money']:
            default['objectives'][which] = op.defaultobjectives(
                project=project, progset=progset, which=which)
        defaults_by_progset_id[progset_id] = default

    return normalize_obj(defaults_by_progset_id)


def get_optimization_from_project(project, optim_id):
    if not isinstance(optim_id, UUID):
        optim_id = UUID(optim_id)

    optims = [
        project.optims[key]
        for key in project.optims
        if project.optims[key].uid == optim_id
    ]
    if not optims:
        raise ValueError("Optimisation does not exist", project_id=project.uid, id=optim_id)
    return optims[0]


def get_optimization_summaries(project):

    optimizations = []

    for o in project.optims.values():

        optim = {
            "id": o.uid,
            "name": o.name,
            "objectives": o.objectives,
            "constraints": o.constraints,
        }

        optim["which"] = o.objectives["which"]

        if o.parsetname:
            optim["parset_id"] = project.parsets[o.parsetname].uid
        else:
            optim["parset_id"] = None

        if o.progsetname:
            optim["progset_id"] = project.progsets[o.progsetname].uid
        else:
            optim["progset_id"] = None

        optimizations.append(optim)

    return optimizations


def set_optimization_summaries_on_project(project, optimization_summaries):
    new_optims = op.odict()

    for summary in optimization_summaries:
        id = summary.get('id', None)

        if id is None:
            optim = op.Optim(project=project)
        else:
            optim = get_optimization_from_project(project, id)

        optim.name = summary["name"]
        optim.parsetname = get_parset_from_project(project, summary["parset_id"]).name
        optim.progsetname = get_progset_from_project(project, summary["progset_id"]).name
        optim.objectives = summary["objectives"]
        optim.objectives["which"] = summary["which"]
        if "constraints" in summary:
            optim.constraints = summary["constraints"]

        new_optims[summary["name"]] = optim

    project.optims = new_optims


