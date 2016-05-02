from collections import defaultdict

from optima.defaults import defaultprograms
from server.webapp.jsonhelper import normalize_obj


"""
Functions to convert Optima objects into JSON-compatible
data structures, both for storing into a database, and
to construct JSON web-packets.
"""


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


