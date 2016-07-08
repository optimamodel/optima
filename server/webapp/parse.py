from numpy.core.numeric import array

_doc_ = """

# parse.py

containcs functions to convert Optima
objects into JSON-compatible data structures, both
for storing into a database, and to construct JSON web-packets.

There should be no references to the database here!

"""

from collections import defaultdict
from pprint import pprint
from numpy import nan

from flask.ext.restful import fields, marshal

from optima import loadpartable, partable, Par
from optima.defaults import defaultprograms

from server.webapp.utils import normalize_obj


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
    print ">> parsing costcovdata"
    pprint(costcovdata, indent=2)
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
        result = {
            't': ccopars['t'],
            'saturation': map(tuple, ccopars['saturation']),
            'unitcost': map(tuple, ccopars['unitcost'])
        }
    return result


def parse_program_summary(program, active):
    result = {
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
    return [parse_program_summary(p, False) for p in defaultprograms(project)]


def get_parameters_from_parset(parset, ind=0):
    """

    Args:
        parset: optima parameterset object

    Returns:
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
                print('Parameter type "%s" not implemented!' % par.fittable)
    return parameters


def put_parameters_in_parset(parameters, parset, i_set=0):
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
            print('Parameter type "%s" not implemented!' % par_type)


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


def parse_parameters_from_progset_parset(settings, progset, parset):
    print ">>> Parsing parameters"

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


def parse_parameters_of_parset_list(parset_list):
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


# WARNING, this should probably not be hard-coded here

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
    maybe_bool = lambda (p): bool(int(p)) if p in ['0', '1'] else p
    result = []
    lines = [l.strip() for l in ALL_POPULATIONS_SOURCE.split('\n')][2:-1]
    for line in lines:
        tokens = line.split(";")
        entry = dict((key, maybe_bool(token)) for key, token in zip(keys, tokens))
        result.append(entry)
    return result


def parse_outcomes_from_progset(progset):
    """
    Args:
        progset: an Optima set of programs

    Returns:
        The outcomes in a list of dictionaries:

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
    """
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


def convert_program_list(program_list):
    result = {}
    for entry in program_list:
        key = entry["program"]
        vals = entry["values"]
        if all(v is None for v in vals):
            continue
        vals = [v if v is not None else 0 for v in vals]
        result[key] = array(vals)
    return result


