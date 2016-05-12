

"""

Functions to convert Optima objects into JSON-compatible
data structures, both for storing into a database, and
to construct JSON web-packets.

There should be no references to the database here!

"""


from collections import defaultdict

from optima.defaults import defaultprograms
from server.webapp.utils import normalize_obj

pluck = lambda l, k: [e[k] for e in l if e[k] is not None]


def parse_targetpars(targetpars):
    parameters = defaultdict(list)
    for parameter in targetpars:
        short = parameter['param']
        pop = parameter['pop']
        parameters[short].append(pop)
    return [
        {
            'active': True,
            'param': short,
            'pops': pop,
        }
        for short, pop
        in parameters.items()
    ]


def revert_targetpars(pars):
    if pars is None:
        return []
    targetpars = []
    for par in pars:
        if par.get('active', False):
            targetpars.extend([
                {
                    'param': par['param'],
                    'pop': pop if type(pop) in (str, unicode) else tuple(pop)
                }
                for pop in par['pops']
            ])
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
        if None in entry.values():
            continue
        if entry['cost'] == 0 or entry['coverage'] == 0:
            continue
        result.append(entry)
    return result


def revert_costcovdata(costcov):
    result = {}
    if costcov is not None:
        result = {
            't': pluck(costcov, 'year'),
            'cost': pluck(costcov, 'cost'),
            'coverage': pluck(costcov, 'coverage'),
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


def parse_program_summary(program):
    result = {
        'active': False,
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


def get_default_program_summaries(project):
    return [parse_program_summary(p) for p in defaultprograms(project)]


def get_parset_parameters(parset, ind=0):
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
            s += pprint.pformat({ key: par }) + "\n"
    return s


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
Females;Other females;0;1;0;15;49;0;0;
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
        result['active'] = False
        result.append(entry)
    return result


def scenario_par(orig_pars):
    if not isinstance(orig_pars, list):
        raise ValueError("needs to be a list.")

    pars = []

    for i in orig_pars:

        pars.append({
            'endval': float(i['endval']),
            'endyear': int(i['endyear']),
            'name': str(i['name']),
            'for': [i['for']],
            'startval': float(i['startval']),
            'startyear': int(i['startyear'])
        })

    return pars


def scenario_program(orig_programs):  # result is either budget or coverage, depending on scenario type
    if not isinstance(orig_programs, list):
        raise ValueError("needs to be a list or dictionaries.")

    if len(orig_programs) == 0:
        return []

    if not isinstance(orig_programs[0], dict):
        raise ValueError("needs to be a list or dictionaries.")

    programs = {}
    for program_entry in orig_programs:
        program_name = str(program_entry['program'])
        values = program_entry['values']
        print('---------')
        print(values)
        if not isinstance(values, list):
            values = [values]
        programs[program_name] = []
        for elem in values:
            programs[program_name].append(float(elem))

    return programs