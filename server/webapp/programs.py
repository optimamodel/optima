from collections import defaultdict

from optima.defaults import defaultprograms
from server.webapp.jsonhelper import normalize_obj


def parse_targetpars(targetpars):
    parameters = defaultdict(list)
    for parameter in targetpars:
        short = parameter['param']
        pop = parameter['pop']
        parameters[short].append(pop)
    pars = [
        {
            'active': True,
            'param': short_name,
            'pops': pop,
        }
        for short_name, pop
        in parameters.iteritems()
    ]
    return pars


def parse_covcovdata(costcovdata):
    if costcovdata is not None:
        result = []
        costcovdata = normalize_obj(costcovdata)
        n_t = len(costcovdata['t'])
        for i_t in range(n_t):
            entry = {
                'year': costcovdata['t'][i_t],
                'cost': costcovdata['cost'][i_t],
                'coverage': costcovdata['coverage'][i_t]
            }
            if None in entry.values():
                continue
            if entry['cost'] == 0 or entry['coverage'] == 0:
                continue
            result.append(entry)
    else:
        result = None
    return result


def parse_program_summary(program, for_fe=False):
    short_name_key = 'short_name' if for_fe else 'short'
    result = {
        'active': False,
        'name': program.name,
        short_name_key: program.short,
        'populations': normalize_obj(program.targetpops),
        'criteria': program.criteria,
        'parameters': parse_targetpars(program.targetpars),
        'ccopars': normalize_obj(program.costcovfn.ccopars),
        'category': program.category,
        'costcov': parse_covcovdata(program.costcovdata),
    }
    return result


def get_default_program_summaries(project, for_fe = False):
    return [parse_program_summary(p, for_fe) for p in defaultprograms(project)]


def program_categories(project):
    result = []
    next_category = None
    for p in get_default_program_summaries(project, for_fe = True):
        current_category = p['category']
        if next_category is not None and next_category['category'] == current_category:
            next_category['programs'].append({'short_name': p['short_name'], 'name': p['name']})
        else:
            if next_category is not None:
                result.append(next_category)
            next_category = {'category':current_category}
            next_category['programs'] = []
    if next_category is not None: result.append(next_category)
    return result

