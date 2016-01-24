from collections import defaultdict

from optima.defaults import defaultprograms


def get_default_programs(parset):

    programs = defaultprograms(parset)
    rv = []

    for program in programs:

        parameters = defaultdict(list)
        for parameter in program.targetpars:
            parameters[parameter['param']].append(parameter['pop'])

        rv.append({
            'active': False,
            'category': program.category,
            'name': program.name,
            'short': program.short,
            'populations': program.targetpops,
            'parameters': [{
                'active': True if pop else False,
                'param': short_name,
                'pops': pop,
            } for short_name, pop in parameters.iteritems()],
            'criteria': program.criteria,
        })

    return rv


def programs_for_input_key(key, programs=None):  # params is the output of parameters.parameters() method
    from parameters import input_parameters
    if not programs or not any(item for item in programs):
        programs = program_list

    params = input_parameters(key)
    result = defaultdict(list)
    keys = None
    for param in params:
        keys = param.get('keys')
        if keys is not None:
            for program in programs:
                program_name = program['short']
                for parameter in program['parameters']:
                    if parameter['param'] == keys:
                        pops = parameter['pop']
                        if pops and pops != ['']:
                            result[program_name].extend(pops)
    return result


def program_categories(project):
    result = []
    next_category = None
    for p in get_default_programs(project):
        current_category = p['category']
        if next_category is not None and next_category['category'] == current_category:
            next_category['programs'].append({'short': p['short'], 'name': p['name']})
        else:
            if next_category is not None:
                result.append(next_category)
            next_category = {'category':current_category}
            next_category['programs'] = []
    if next_category is not None: result.append(next_category)
    return result

