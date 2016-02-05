from collections import defaultdict

from optima.defaults import defaultprograms

def get_default_programs(project, for_fe = False):

    programs = defaultprograms(project)
    rv = []
    short_name_key = 'short_name' if for_fe else 'short'
    for program in programs:

        parameters = defaultdict(list)
        for parameter in program.targetpars:
            parameters[parameter['param']].append(parameter['pop'])

        rv.append({
            'active': False,
            'category': program.category,
            'name': program.name,
            short_name_key: program.short,
            'populations': program.targetpops,
            'parameters': [{
                'active': True if pop else False,
                'param': short_name,
                'pops': pop,
            } for short_name, pop in parameters.iteritems()],
            'criteria': program.criteria,
        })
#        print "rv", rv
    return rv


def program_categories(project):
    result = []
    next_category = None
    for p in get_default_programs(project, for_fe = True):
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

