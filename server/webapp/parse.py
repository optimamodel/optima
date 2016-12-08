"""
parse.py
========

Functions to convert/revert Optima objects into JSON-compatible data structures.

Nomenclature:
 - get_*_from_* to extract data structures
 - set_*_on_* to modify a PyOptima object with data structure

There should be no references to the database or web-handlers.
"""

from collections import defaultdict, OrderedDict
from pprint import pprint, pformat
from uuid import UUID

import numpy as np
import optima as op

from .exceptions import ParsetDoesNotExist, ProgramDoesNotExist, ProgsetDoesNotExist


def print_odict(name, an_odict):
    """
    Helper function to print an odict to the console
    """
    print(">> %s = <odict>" % name)
    obj = normalize_obj(an_odict)
    s = pformat(obj, indent=2)
    for line in s.splitlines():
        print(">> " + line)


def normalize_obj(obj):
    """
    This is the main conversion function for Python data-structures into
    JSON-compatible data structures.

    Use this as much as possible to guard against data corruption!

    Args:
        obj: almost any kind of data structure that is a combination
            of list, numpy.ndarray, odicts etc

    Returns:
        A converted dict/list/value that should be JSON compatible
    """

    if isinstance(obj, list) or isinstance(obj, np.ndarray) or isinstance(obj, tuple):
        return [normalize_obj(p) for p in list(obj)]

    if isinstance(obj, dict):
        return {str(k): normalize_obj(v) for k, v in obj.items()}

    if isinstance(obj, op.utils.odict):
        result = OrderedDict()
        for k, v in obj.items():
            result[str(k)] = normalize_obj(v)
        return result

    if isinstance(obj, np.bool_):
        return bool(obj)

    if isinstance(obj, float):
        if np.isnan(obj):
            return None

    if isinstance(obj, np.float64):
        if np.isnan(obj):
            return None
        else:
            return float(obj)

    if isinstance(obj, unicode):
        return str(obj)

    if isinstance(obj, set):
        return list(obj)

    return obj



# PROJECTS

def get_project_years(project):
    settings = project.settings
    return range(int(settings.start), int(settings.end) + 1)


ALL_POPULATIONS_SOURCE = """
Short name;Full name;Male;Female;AgeFrom;AgeTo;
FSW;Female sex workers;0;1;15;49;
Clients;Clients of sex workers;1;0;15;49;
MSM;Men who have sex with men;1;0;15;49;
Transgender;Transgender individuals;0;0;15;49;
PWID;People who inject drugs;0;0;15;49;
Male PWID;Males who inject drugs;1;0;15;49;
Female PWID;Females who inject drugs;0;1;15;49;
Children;Children;0;0;2;15;
Infants;Infants;0;0;0;2;
Males;Other males;1;0;15;49;
Females;Other females;0;1;15;49;
Other males;Other males [enter age];1;0;0;0;
Other females;Other females [enter age];0;1;0;0;
"""

keys = "short name male female age_from age_to".split()


def get_default_populations():
    """
    Returns a dictionary of populations with format
    described in `get_populations_from_project`
    """
    result = []
    lines = [l.strip() for l in ALL_POPULATIONS_SOURCE.split('\n')][2:-1]
    for line in lines:
        tokens = line.split(";")
        result.append(dict(zip(keys, tokens)))
    for piece in result:
        for key in ['age_from', 'age_to']:
            piece[key] = int(piece[key])
        for key in "male female".split():
            piece[key] = bool(int(piece[key]))
    return result


def get_populations_from_project(project):
    """
    Returns a dictionary for the project populations, with
    structure modeled after the `pops` parameter
    in `optima.makespreadsheets`:
        -
            short: string
            name: string
            male: bool
            female: bool
            age_from: int
            age_to: int
        - ...
    """
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
        }
        if 'injects' in data_pops:
            population['injects'] = bool((data_pops['injects'][i]))
        if 'sexworker' in data_pops:
            population['sexworker'] = bool((data_pops['sexworker'][i]))
        populations.append(population)
    return populations


def revert_populations_to_pop(populations):
    """
    Reverts the population dictionary from `get_populations_from_project`
    to the structure expected for `project.data['pops']` in a project:
         <odict>
             - short:
                - 'FSW'
                - 'Clients'
                - 'MSM'
                - 'PWID'
                - 'M 15+'
                - 'F 15+'
             - long:
                - 'Female sex workers'
                - 'Clients of sex workers'
                - 'Men who have sex with men'
                - 'People who inject drugs'
                - 'Males 15+'
                - 'Females 15+'
             - male: [0, 1, 1, 1, 1, 0]
             - female: [1, 0, 0, 0, 0, 1]
             - age:
                - [15, 49]
                - [15, 49]
                - [15, 49]
                - [15, 49]
                - [15, 49]
                - [15, 49]
    """
    data_pops = op.odict()

    for key in ['short', 'long', 'male', 'female', 'age']:
        data_pops[key] = []

    for pop in populations:
        data_pops['short'].append(pop['short'])
        data_pops['long'].append(pop['name'])
        data_pops['male'].append(int(pop['male']))
        data_pops['female'].append(int(pop['female']))
        data_pops['age'].append((int(pop['age_from']), int(pop['age_to'])))

    return data_pops


def clear_project_data(project):
    print(">> Deleting project.data")
    project.data = {}
    project.progsets.clear()
    project.parsets.clear()
    project.scens.clear()
    project.optims.clear()


def set_project_summary_on_project(project, summary):

    print(">> Update project")

    data_pops = revert_populations_to_pop(summary['populations'])

    project.data["pops"] = data_pops
    project.data["npops"] = len(data_pops)

    project.name = summary["name"]

    if not project.settings:
        project.settings = op.Settings()

    dataStart = summary['dataStart']
    dataEnd = summary['dataEnd']
    project.data["years"] = (dataStart, dataEnd)
    project.settings.start = dataStart
    project.settings.end = dataEnd


def is_progset_optimizable(progset):
    """
    Returns whether the progset has enough parameters to
    carry out an optimization, or budget/coverage scenario
    analysis.
    """
    n_program = len(progset.programs.values())
    has_ccopars = progset.hasallcostcovpars()
    has_covout = progset.hasallcovoutpars()
    print(">> Check optimizability, progset %s, %s, %s" % (progset.name, has_ccopars, has_covout))
    if n_program > 0 and has_ccopars and has_covout:
        for program in progset.programs.values():
            if not program.costcovdata.get('t', False):
                return False
        return True
    else:
        return False


def get_project_summary_from_project(project):
    years = project.data.get('years')
    if years:
        data_start = years[0]
        data_end = years[-1]
    else:
        data_start = project.settings.start
        data_end = project.settings.end

    is_ready_to_optimize = True
    n_program = 0
    for progset in project.progsets.values():
        n_program_in_progset = 0
        n_program_in_progset = len(progset.programs)
        if not is_progset_optimizable(progset):
            is_ready_to_optimize = False
        if n_program_in_progset > n_program:
            n_program = n_program_in_progset
    if len(project.progsets.values()) == 0:
        is_ready_to_optimize = False

    project_summary = {
        'id': project.uid,
        'name': project.name,
        'dataStart': data_start,
        'dataEnd': data_end,
        'version': project.version,
        'populations': get_populations_from_project(project),
        'creationTime': project.created,
        'updatedTime': project.modified,
        'dataUploadTime': project.spreadsheetdate,
        'hasParset': len(project.parsets) > 0,
        'isOptimizable': is_ready_to_optimize,
        'nProgram': n_program,
        'hasEcon': "econ" in project.data
    }

    return project_summary


# PARSETS

def get_parameters_from_parset(parset, ind=0):
    """
    Returns a flat dictionary of parameters for the calibration
    page from an optima parameter set object. Extracts subkey's
    for sub-population parameter values, and constructs a unique
    label for each parameter. The structure is:
        -
            value: 13044975.57899749,
            type: exp,
            subkey: Males 15-49,
            key: popsize,
            label: Population size -- Males 15-49
        -
            value: 0.7,
            type: const,
            subkey: null,
            key: recovgt350,
            label: Treatment recovery rate into CD4>350 (%/year)
        - ...
    """
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
            "updated": parset.modified,
            "created": parset.created,
            "name": parset.name
        })
    return parset_summaries


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


def make_pop_label(pop):
    return ' - '.join(pop) if isinstance(pop, tuple) else pop


def get_par_limits(project, par):
    """
    Returns limits of a par [lower, upper]
    """
    def convert(limit):
        if isinstance(limit, str):
            return project.settings.convertlimits(limits=limit)
        else:
            return limit
    return map(convert, par.limits)


def get_parameters_for_scenarios(project, start_year=None):
    """
    Returns parameters that can be modified in a scenario:
        <parsetID>:
            <year>:
                - short: string
                - name: string
                - pop: string -or- list of two string
                - popLabel: string
                - limits: [number, number]
                - startVal: number
    """
    print(">> Get parameters for scenarios")
    if start_year is None:
        start_year = project.settings.start
        end_year = project.settings.end
        years = range(int(start_year), int(end_year) + 1)
    result = {}
    for id, parset in project.parsets.items():
        parset_id = str(parset.uid)
        result[parset_id] = {}
        for year in years:
            pars = []
            result[parset_id][year] = pars
            for par in parset.pars[0].values():
                if not hasattr(par, 'y') or not par.visible:
                    continue
                for pop in par.y.keys():
                    try:
                        par_defaults = op.setparscenvalues(
                            parset, par.short, pop, year)
                        startval = par_defaults['startval']
                        if np.isnan(startval):
                            startval = None
                    except:
                        startval = None
                    pars.append({
                        'name': par.name,
                        'short': par.short,
                        'pop': pop,
                        'popLabel': make_pop_label(pop),
                        'limits': get_par_limits(project, par),
                        'startval': startval
                    })
    print(">> Finished calculating startvals for parameters")
    return result


def get_parameters_for_edit_program(project):
    parameters = []
    added_par_keys = set()
    default_par_keys = [par['short'] for par in op.loadpartable(op.partable)]
    for parset in project.parsets.values():
        for pars in parset.pars:
            for par_key in default_par_keys:
                if par_key in added_par_keys or par_key not in pars:
                    continue
                par = pars[par_key]
                if not isinstance(pars[par_key], op.Par):
                    continue
                if not par.visible == 1 or not par.y.keys():
                    continue
                parameters.append({
                    'name': par.name,
                    'param': par.short,
                    'by': par.by,
                    'pships': par.y.keys() if par.by == 'pship' else []
                })
                added_par_keys.add(par_key)
    return parameters


def get_parameters_for_outcomes(project, progset_id, parset_id):
    progset = get_progset_from_project(project, progset_id)
    parset = get_parset_from_project(project, parset_id)

    print ">> Fetching target parameters from progset '%s'" % progset.name

    progset.gettargetpops()
    progset.gettargetpars()
    progset.gettargetpartypes()

    target_par_shorts = set([p['param'] for p in progset.targetpars])
    pars = parset.pars[0]
    parameters = [
        {
            'short': par_short,
            'name': pars[par_short].name,
            'coverage': pars[par_short].coverage,
            'limits': get_par_limits(project, pars[par_short]),
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


# PROGRAMS


def get_budgets_for_scenarios(project):
    print(">> Get default budges for scenarios")
    result = {
        str(progset.uid): normalize_obj(progset.getdefaultbudget())
        for progset in project.progsets.values()}
    return result


def get_coverages_for_scenarios(project, year=None):
    """
    Returns a dictionary for default coverages for each
    progset and parset:
        <parset_id>:
            <progset_id>:
                <year>:
                    <program_short>: coverage (float)
    """
    print(">> Get default coverages for scenarios")
    result = {}
    start = project.settings.start
    end = project.settings.end
    years = range(int(start), int(end) + 1)
    for parset in project.parsets.values():
        parset_id = str(parset.uid)
        result[parset_id] = {}
        for progset in project.progsets.values():
            progset_id = str(progset.uid)
            result[parset_id][progset_id] = {}
            for year in years:
                try:
                    coverage = progset.getdefaultcoverage(t=year, parset=parset)
                    coverage = normalize_obj(coverage)
                except:
                    coverage = None
                result[parset_id][progset_id][year] = coverage
    return result


def convert_program_targetpars(targetpars):
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


def revert_program_targetpars(pars):
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


def extract_key_i(data, key, i):
    """
    Safely extracts from (key, i) from a data structure
      data = { <key>: [list of values] }
    and returns None if unable to
    """
    try:
        return data[key][i]
    except:
        return None


def convert_program_costcovdata(costcovdata):
    if costcovdata is None:
        return None
    result = []
    costcovdata = normalize_obj(costcovdata)
    n_year = len(costcovdata['t'])
    for i_year in range(n_year):
        entry = {}
        for source_key, target_key in [
               ('t', 'year'), ('cost', 'cost'), ('coverage', 'coverage')]:
            entry[target_key] = extract_key_i(costcovdata, source_key, i_year)
        if entry["cost"] is None and entry["coverage"] is None:
            continue
        result.append(entry)
    return result


pluck = lambda l, k: [e[k] for e in l]
to_nan = lambda v: v if v is not None and v != "" else np.nan


def revert_program_costcovdata(costcov):
    result = {}
    if costcov:
        costcov = normalize_obj(costcov)
        result = {
            't': map(to_nan, pluck(costcov, 'year')),
            'cost': map(to_nan, pluck(costcov, 'cost')),
            'coverage': map(to_nan, pluck(costcov, 'coverage')),
        }
    return result


def revert_program_ccopars(ccopars):
    result = None
    if ccopars:
        result = op.odict({
            't': ccopars['t'],
            'saturation': map(tuple, ccopars['saturation']),
            'unitcost': map(tuple, ccopars['unitcost'])
        })
    return result


def split_pair(val):
    if val is None:
        return (None, None)
    if isinstance(val, float) or isinstance(val, int):
        return (val, val)
    else:
        return val


def get_program_summary(program, progset, active):
    """
    Returns a dictionary for a program:
        name: HIV testing and counseling,
        short: HTC,
        active: True,
        id: 9b5db736-1026-11e6-8ffc-f36c0fc28d89,
        category: Care and treatment,
        progset_id: 9b55945c-1026-11e6-8ffc-130aba4858d2,
        project_id: 9b118ef6-1026-11e6-8ffc-571b10a45a1c,
        created: Mon, 02 May 2016 05:27:48 -0000,
        updated: Mon, 02 May 2016 06:22:29 -0000
        attr: { dictionary to hold CostCovGraph parameters }
        optimizable: True,
        ccopars:
            saturation:
                - [0.9, 0.9]
            t:
                - 2016
            unitcost:
                - [1.136849845773715, 1.136849845773715]
        costcov:
            -
                cost: 16616289
                coverage: 8173260
                year: 2012},
            -
                cost: 234234
                coverage: 324234
                year: 2013,
        criteria:
            hivstatus: allstates
            pregnant: False
        populations:
            - FSW,
            - Clients,
            - Male Children 0-14,
            - Female Children 0-14,
            - Males 15-49,
            - Females 15-49,
            - Males 50+,
            - Females 50+],
        targetpars:
            -
                active: True,
                param: hivtest,
                pops:
                    - FSW,
                    - Clients,
                    - Male Children 0-14,
                    - Female Children 0-14,
                    - Males 15-49,
                    - Females 15-49,
                    - Males 50+,
                    - Females 50+
            """

    ccopars_dict = normalize_obj(program.costcovfn.ccopars)
    for key in ['saturation', 'unitcost']:
        if key not in ccopars_dict:
            continue
        a_list = ccopars_dict[key]
        n = len(a_list)
        for i in range(n):
            a_list[i] = split_pair(a_list[i])

    result = {
        'id': program.uid,
        'progset_id': progset.uid if progset is not None else None,
        'active': active,
        'name': program.name,
        'short': program.short,
        'populations': normalize_obj(program.targetpops),
        'criteria': program.criteria,
        'targetpars': convert_program_targetpars(program.targetpars),
        'ccopars': ccopars_dict,
        'category': program.category,
        'costcov': convert_program_costcovdata(program.costcovdata),
        'optimizable': program.optimizable()
    }
    if hasattr(program, "attr"):
        result["attr"] = program.attr
    return result


def get_default_program_summaries(project):
    return [
        get_program_summary(p, None, False)
        for p in op.defaults.defaultprograms(project)]


# PROGSET OUTCOMES

def get_outcome_summaries_from_progset(progset):
    """
    Returns a list of dictionaries for progset outcomes:
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
          ...
        ]
    """
    outcomes = []
    for par_short in progset.targetpartypes:
        pop_keys = progset.progs_by_targetpar(par_short).keys()
        for pop_key in pop_keys:
            covout = progset.covout[par_short][pop_key]
            outcome = {
                'name': par_short,
                'pop': pop_key,
                'interact': covout.interaction,
                'years': []
            }
            n_year = len(covout.ccopars.get('t', []))
            for i_year in range(n_year):
                intercept = extract_key_i(covout.ccopars, 'intercept', i_year)
                intercept = split_pair(intercept)
                year = {
                    'intercept_upper': intercept[1],
                    'intercept_lower': intercept[0],
                    'year': extract_key_i(covout.ccopars, 't', i_year),
                    'programs': []
                }
                for program_name, program_intercepts in covout.ccopars.items():
                    if program_name in ['intercept', 't', 'interact']:
                        continue
                    if len(program_intercepts) > i_year:
                        pair = split_pair(program_intercepts[i_year])
                    else:
                        pair = (None, None)
                    program = {
                        'name': program_name,
                        'intercept_lower': pair[0],
                        'intercept_upper': pair[1],
                    }
                    year['programs'].append(program)

                outcome['years'].append(year)
            outcomes.append(outcome)
    return outcomes


def set_outcome_summaries_on_progset(outcomes, progset):

    for covout_by_poptuple in progset.covout.values():
        for covout in covout_by_poptuple.values():
            covout.ccopars = op.odict()

    for outcome in outcomes:
        for year in outcome['years']:
            par_short = outcome['name']
            if par_short not in progset.covout:
                continue
            covout_by_poptuple = progset.covout[par_short]

            ccopar = {
                'intercept': (year['intercept_lower'], year['intercept_upper']),
                't': int(year['year']),
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
            if poptuple in covout_by_poptuple:
                covout_by_poptuple[poptuple].addccopar(ccopar, overwrite=True)

            covout_by_poptuple[poptuple].interaction = outcome['interact']


# PROGETS


def get_progset_summary(project, progset_name):
    """
    Returns a summary of a progset:
        id: uid
        name: string
        created: datetime
        updated: datetime
        programs: <program_summaries>
        isOptimizable: boolean

    """
    progset = project.progsets[progset_name]

    active_program_summaries = [
        get_program_summary(p, progset=progset, active=True)
        for p in progset.programs.values()]
    inactive_program_summaries = [
        get_program_summary(p, progset=progset, active=False)
        for p in getattr(progset, "inactive_programs", {}).values()]
    program_summaries = active_program_summaries + inactive_program_summaries

    # Overwrite with default name and category if applicable
    default_program_summaries = get_default_program_summaries(project)
    loaded_program_shorts = []
    default_program_summary_by_short = {
        p['short']: p for p in default_program_summaries}
    for program_summary in program_summaries:
        short = program_summary['short']
        if short in default_program_summary_by_short:
            default_program_summary = default_program_summary_by_short[short]
            if not program_summary['name']:
                program_summary['name'] = default_program_summary['name']
            program_summary['category'] = default_program_summary['category']
        loaded_program_shorts.append(short)

    # append any default programs as inactive if not already in project
    for program_summary in default_program_summaries:
        if program_summary['short'] not in loaded_program_shorts:
            program_summaries.append(program_summary)

    for program_summary in program_summaries:
        if program_summary['category'] == 'No category':
            program_summary['category'] = 'Other'
        if not program_summary['name']:
            program_summary['name'] = program_summary['short']

    print(">> Extract progset summary %s-%s " % (project.name, progset.name))
    progset_summary = {
        'id': progset.uid,
        'name': progset.name,
        'created': progset.created,
        'updated': progset.modified,
        'programs': program_summaries,
        'isOptimizable': is_progset_optimizable(progset),
    }
    return normalize_obj(progset_summary)


def get_progset_summaries(project):
    print(">> Get progset summaries")
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
        program_id = summary.get("id")
        if program_id is None:
            raise ProgramDoesNotExist

        program = get_program_from_progset(progset, program_id, include_inactive=True)

        # It exists, so remove it first...
        try:
            progset.programs.pop(program.short)
        except KeyError:
            progset.inactive_programs.pop(program.short)

        program_id = program.uid
    except ProgramDoesNotExist:
        program_id = None
        pass

    if "ccopars" in summary:
        ccopars = revert_program_ccopars(summary["ccopars"])
    else:
        ccopars = None

    if "targetpars" in summary:
        targetpars = revert_program_targetpars(summary["targetpars"])
    else:
        targetpars = None

    if "costcov" in summary:
        costcov = revert_program_costcovdata(summary["costcov"])
    else:
        costcov = None

    program = op.Program(
        short=summary["short"],
        name=summary["name"],
        category=summary["category"],
        targetpars=targetpars,
        targetpops=summary["populations"],
        criteria=summary["criteria"],
        ccopars=ccopars,
        costcovdata=costcov)

    if "attr" in summary:
        program.attr = summary["attr"]

    if program_id:
        program.uid = program_id

    if summary["active"]:
        progset.addprograms(program)
    else:
        progset.inactive_programs[program.short] = program

    progset.updateprogset()


def get_progset_from_name(project, progset_name, progset_id=None):
    print(">> Finding progset '%s'" % progset_name)
    if progset_name not in project.progsets:
        if progset_id:
            print("> Updated program set %s with new id %s" % (progset_name, progset_id))
            # It may have changed, so try getting via ID if we have it...
            progset = get_progset_from_project(project, progset_id)
            project.progsets.pop(progset.name)

            # Update the name and its reflection in the project.
            progset.name = progset_name
            project.progsets[progset_name] = progset
        else:
            print("> Created program set %s" % progset_name)
            project.progsets[progset_name] = op.Programset(name=progset_name)
    return project.progsets[progset_name]


def set_progset_summary_on_progset(progset, progset_summary):
    # Clear the current programs...
    progset.programs = op.odict()
    progset.inactive_programs = op.odict()
    print(">> Setting %d programs on progset" % len(progset_summary['programs']))
    for p in progset_summary['programs']:
        set_program_summary_on_progset(progset, p)
    progset.updateprogset()


def set_progset_summary_on_project(project, progset_summary, progset_id=None):
    """
    Updates/creates a progset from a progset_summary, with the addition
    of inactive_programs that are taken from the default programs
    generated from pyOptima.
    """
    progset = get_progset_from_name(project, progset_summary['name'], progset_id)
    set_progset_summary_on_progset(progset, progset_summary)


# SCENARIOS


def force_tuple_list(item):
    if isinstance(item, str) or isinstance(item, unicode):
        return [str(item)]
    if isinstance(item, list):
        if len(item) == 1:
            # this is for the weird case of ['tot']
            return str(item[0])
        elif len(item) == 2:
            # looks like a partnership
            return tuple(map(str, item))
    return item


def convert_scenario_pars(pars):
    result = []
    for par in pars:
        result.append({
            'name': par.get('name', ''),
            'startyear': par.get('startyear', None),
            'endval': par.get('endval', None),
            'endyear': par.get('endyear', None),
            'startval': par.get('startval', None),
            'for': par['for'][0] if len(par['for']) == 1 else par['for']
        })
    return result


def revert_scenario_pars(pars):
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


def convert_program_list(program_list):
    items = program_list.items()
    return [{"program": x, "values": y} for x, y in items]


def revert_program_list(program_list):
    result = {}
    for entry in program_list:
        key = entry["program"]
        vals = entry["values"]
        if all(v is None for v in vals):
            continue
        vals = [v if v is not None else 0 for v in vals]
        result[key] = np.array(vals)
    return result



def get_scenario_summary(project, scenario):
    """
    Returns dictionary for scenario:
        id: uuid_string
        progset_id: uuid_string -or- null # since parameter scenarios don't have progsets
        parset_id: uuid_string
        name: string
        active: boolean
        years: list of number
        scenario_type: "parameter", "coverage" or "budget"
         -EITHER-
        pars:
            - name: string
              for: string -or- [1 string] -or- [2 strings]
              startyear: number
              endyear: number
              startval: number
              endval: number
            - ...
         -OR-
        budget:
            - program: string
              values: [number -or- null] # same length as years
            - ...
         -OR-
        coverage:
            - program: string
              values: [number -or- null] # same length as years
            - ...
    """
    variant_data = {}

    # budget, coverage, parameter, any others?
    if isinstance(scenario, op.Parscen):
        scenario_type = "parameter"
        variant_data["pars"] = convert_scenario_pars(scenario.pars)
    elif isinstance(scenario, op.Coveragescen):
        scenario_type = "coverage"
        variant_data["coverage"] = convert_program_list(scenario.coverage)
    elif isinstance(scenario, op.Budgetscen):
        scenario_type = "budget"
        variant_data["budget"] = convert_program_list(scenario.budget)

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
    result.update(variant_data)
    return result


def get_scenario_summaries(project):
    print(">> Get scenario summaries")
    scenario_summaries = []
    for scen in project.scens.values():
        summary = get_scenario_summary(project, scen)
        scenario_summaries.append(summary)
    return normalize_obj(scenario_summaries)


def set_scenario_summaries_on_project(project, scenario_summaries):
    # delete any records with id's that aren't in summaries

    project.scens = op.odict()

    for summary in scenario_summaries:

        if summary["parset_id"]:
            parset = get_parset_from_project(project, summary["parset_id"])
            parset_name = parset.name
        else:
            parset_name = None

        if summary["scenario_type"] == "parameter":

            kwargs = {
                "name": summary["name"],
                "parsetname": parset_name,
                'pars': revert_scenario_pars(summary.get('pars', []))
            }
            scen = op.Parscen(**kwargs)

        else:

            if "progset_id" in summary and summary["progset_id"]:
                progset = get_progset_from_project(project, summary["progset_id"])
                progset_name = progset.name
            else:
                progset_name = None

            kwargs = {
                "name": summary["name"],
                "parsetname": parset_name,
                "progsetname": progset_name,
                "t": summary.get("years")
            }

            if summary["scenario_type"] == "coverage":

                kwargs.update(
                    {'coverage': revert_program_list(summary.get('coverage', []))})
                scen = op.Coveragescen(**kwargs)

            elif summary["scenario_type"] == "budget":

                kwargs.update(
                    {'budget': revert_program_list(summary.get('budget', []))})
                scen = op.Budgetscen(**kwargs)

        if summary.get("id"):
            scen.uid = UUID(summary["id"])

        scen.active = summary["active"]
        project.scens[scen.name] = scen



# OPTIMIZATIONS


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
    '''
    Returns a list of dictionaries:
        -
            name: Optimization 1,
            which: outcomes
            parset_id: af6847d6-466b-4fc7-9e41-1347c053a0c2,
            progset_id: cfa49dcc-2b8b-11e6-8a08-57d606501764,
            constraints:
                max:
                    ART: None,
                    Condoms: None,
                    FSW programs: None,
                    HTC: None,
                    Other: 1,
                min:
                    ART: 1,
                    Condoms: 0,
                    FSW programs: 0,
                    HTC: 0,
                    Other: 1,
                name:
                    ART: Antiretroviral therapy,
                    Condoms: Condom promotion and distribution,
                    FSW programs: Programs for female sex workers and clients,
                    HTC: HIV testing and counseling,
                    Other: Other,
            objectives:
                base: None,
                budget: 60500000,
                deathfrac: None,
                deathweight: 5,
                end: 2030,
                incifrac: None,
                inciweight: 1,
                keylabels:
                    death: Deaths
                    inci: New infections,
                keys:
                    - death
                    - inci
                start: 2017,
                which: outcomes,
        -...
     '''
    optim_summaries = []

    for optim in project.optims.values():

        optim_summary = {
            "id": optim.uid,
            "name": optim.name,
            "objectives": optim.objectives,
            "constraints": optim.constraints,
        }

        optim_summary["which"] = optim.objectives["which"]

        if optim.parsetname:
            optim_summary["parset_id"] = project.parsets[optim.parsetname].uid
        else:
            optim_summary["parset_id"] = None

        if optim.progsetname:
            progset = project.progsets[optim.progsetname]
            optim_summary["progset_id"] = progset.uid
        else:
            progset = project.progsets[0]
            optim_summary["progset_id"] = progset.uid

        default_constraints = op.defaultconstraints(project=project, progset=progset)
        constraints = optim_summary["constraints"]

        default_prog_keys = default_constraints["name"].keys()
        for prog_key in default_prog_keys:
            if prog_key not in constraints["name"]:
                for attr in ["name", "max", "min"]:
                    constraints[attr][prog_key] = default_constraints[attr][prog_key]

        for prog_key in constraints["name"].keys():
            if prog_key not in default_prog_keys:
                for attr in ["name", "max", "min"]:
                    del constraints[attr][prog_key]

        print(">> Optim constraints", optim.constraints)
        optim_summaries.append(optim_summary)

    return optim_summaries


def set_optimization_summaries_on_project(project, optimization_summaries):
    new_optims = op.odict()

    for summary in optimization_summaries:
        id = summary.get('id', None)

        if id is None:
            optim = op.Optim(project=project)
            print(">> Creating new optimization '%s'" % optim.uid)
        else:
            print(">> Updating optimization '%s'" % id)
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


def get_parset_from_project_by_id(project, parset_id):
    for key, parset in project.parsets.items():
        if str(parset.uid) == str(parset_id):
            return parset
    else:
        return None


# PORTFOLIOS


def get_portfolio_summary(portfolio):
    gaoptim_summaries = []
    objectivesList = []
    for gaoptim_key, gaoptim in portfolio.gaoptims.items():
        resultpairs_summary = []
        for resultpair_key, resultpair in gaoptim.resultpairs.items():
            resultpair_summary = {}
            for result_key, result in resultpair.items():
                result_summary = {
                    'name': result.name,
                    'id': result.uid,
                }
                resultpair_summary[result_key] = result_summary
            resultpairs_summary.append(resultpair_summary)

        gaoptim_summaries.append({
            "key": gaoptim_key,
            "objectives": dict(gaoptim.objectives),
            "id": gaoptim.uid,
            "name": gaoptim.name,
            "resultpairs": resultpairs_summary
        })

        objectivesList.append(gaoptim.objectives)

    project_summaries = []

    for project in portfolio.projects.values():
        boc = project.getBOC(objectivesList[0])
        project_summary = {
            'name': project.name,
            'id': project.uid,
            'boc': 'calculated' if boc is not None else 'not ready',
            'results': []
        }
        for result in project.results.values():
            project_summary['results'].append({
                'name': result.name,
                'id': result.uid
            })
        project_summaries.append(project_summary)

    result = {
        "created": portfolio.created,
        "name": portfolio.name,
        "gaoptims": gaoptim_summaries,
        "id": portfolio.uid,
        "version": portfolio.version,
        "gitversion": portfolio.gitversion,
        "outputstring": '',
        "projects": project_summaries,
    }

    if hasattr(portfolio, "outputstring"):
        result["outputstring"] = portfolio.outputstring.replace('\t', ',')

    return result


def set_portfolio_summary_on_portfolio(portfolio, summary):
    """
    Saves the summary result onto the portfolio and returns
    a list of project_ids of projects that are not in the portfolio
    """
    gaoptim_summaries = summary['gaoptims']
    gaoptims = portfolio.gaoptims
    for gaoptim_summary in gaoptim_summaries:
        gaoptim_id = str(gaoptim_summary['id'])
        objectives = op.odict(gaoptim_summary["objectives"])
        if gaoptim_id in gaoptims:
            gaoptim = gaoptims[gaoptim_id]
            gaoptim.objectives = objectives
        else:
            gaoptim = op.portfolio.GAOptim(objectives=objectives)
            gaoptims[gaoptim_id] = gaoptim
    old_project_ids = portfolio.projects.keys()
    print("> old project ids %s" % old_project_ids)
    project_ids = [s["id"] for s in summary["projects"]]
    print("> new project ids %s" % project_ids)
    for old_project_id in old_project_ids:
        if old_project_id not in project_ids:
            portfolio.projects.pop(old_project_id)

    new_project_ids = []
    for project_id in project_ids:
        if project_id not in portfolio.projects:
            new_project_ids.append(project_id)

    return new_project_ids


