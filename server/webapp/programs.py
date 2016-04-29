from collections import defaultdict

from optima.defaults import defaultprograms
from server.webapp.jsonhelper import normalize_obj


def parse_targetpars(targetpars):
    parameters = defaultdict(list)
    for parameter in targetpars:
        short = parameter['param']
        pop = parameter['pop']
        parameters[short].append(pop)
    return [
        {
            'active': True,
            'param': short_name,
            'pops': pop,
        }
        for short_name, pop
        in parameters.items()
    ]


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


def parse_program(program, for_fe=False):
    short_name_key = 'short_name' if for_fe else 'short'
    result = {
        'active': False,
        'name': program.name,
        short_name_key: program.short,
        'populations': normalize_obj(program.targetpops),
        'criteria': program.criteria,
        'parameters': parse_targetpars(program.targetpars),
        'targetpops': normalize_obj(program.targetpops),
        'ccopars': normalize_obj(program.costcovfn.ccopars),
        'category': program.category,
        'costcov': parse_costcovdata(program.costcovdata),
    }
    return result


def get_default_program_summaries(project, for_fe=False):
    return [parse_program(p, for_fe) for p in defaultprograms(project)]


def print_program(program):
    pprint({
        'short': program.short,
        'name': program.name,
        'targetpars': program.targetpars,
        'category': program.category,
        'targetpops': program.targetpops,
        'criteria': program.criteria,
        'costcovdata': normalize_obj(program.costcovdata),
        'costcovfn.ccopars': normalize_obj(program.costcovfn.ccopars)
    })

