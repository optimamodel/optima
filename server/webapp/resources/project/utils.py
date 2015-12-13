from copy import deepcopy


def getPopsAndProgsFromModel(project_entry, trustInputMetadata):
    """
    Initializes "meta data" about populations and programs from model.
    keep_old_parameters (for program parameters)
    will be True if we import from Excel.
    """
    from sim.programs import programs
    from sim.populations import populations
    programs = programs()
    populations = populations()
    model = project_entry.model
    if 'data' not in model:
        return

    dict_programs = dict([(item['short_name'], item) for item in programs])

    # Update project_entry.populations and project_entry.programs
    D_pops = model['data']['meta']['pops']
    D_progs = model['data']['meta']['progs']
    D_pops_names = model['data']['meta']['pops']['short']
    D_progs_names = model['data']['meta']['progs']['short']
    old_programs_dict = dict(
        [(item.get('short_name') if item else '', item) for item in project_entry.programs])

    # get and generate populations from D.data.meta
    pops = []
    if trustInputMetadata and model['G'].get('inputpopulations'):
        pops = deepcopy(model['G']['inputpopulations'])
    else:
        for index, short_name in enumerate(D_pops_names):
            new_item = {}
            new_item['name'] = D_pops['long'][index]
            new_item['short_name'] = short_name
            for prop in ['sexworker', 'injects', 'sexmen', 'client', 'female', 'male', 'sexwomen']:
                new_item[prop] = bool(D_pops[prop][index])
            pops.append(new_item)

    # get and generate programs from D.data.meta
    progs = []
    if trustInputMetadata and model['G'].get('inputprograms'):
        # if there are already parameters
        progs = deepcopy(model['G']['inputprograms'])
    else:
        # we should try to rebuild the inputprograms
        for index, short_name in enumerate(D_progs_names):
            new_item = {}
            new_item['name'] = D_progs['long'][index]
            new_item['short_name'] = short_name
            new_item['parameters'] = []
            new_item['category'] = 'Other'
            old_program = old_programs_dict.get(short_name)
            # if the program was given in create_project, keep the parameters
            if old_program:
                new_item['category'] = old_program['category']
                new_item['parameters'] = deepcopy(old_program['parameters'])
            else:
                standard_program = dict_programs.get(short_name)
                if standard_program:
                    new_item['category'] = standard_program['category']
                    new_parameters = [{'value': parameter}
                                      for parameter in standard_program['parameters']]
                    for parameter in new_parameters:
                        if parameter['value']['pops'] == ['']:
                            parameter['value']['pops'] = list(D_pops_names)
                    if new_parameters:
                        new_item['parameters'] = deepcopy(new_parameters)

            progs.append(new_item)

    project_entry.populations = pops
    project_entry.programs = progs
    years = model['data']['epiyears']
    # this is the new truth
    model['G']['inputprograms'] = progs
    model['G']['inputpopulations'] = pops
    project_entry.model = model
    project_entry.datastart = int(years[0])
    project_entry.dataend = int(years[-1])
