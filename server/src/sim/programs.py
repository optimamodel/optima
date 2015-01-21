ALL_PROGRAMS_SOURCE = \"""Short name;Full program name;Category;Parameter 1;Parameter 2;Parameter 3;Par. 1 name;Par. 1 pop;Par. 2 name;Par. 2 pop;Par. 3 name;Par. 3 pop;;;;;;;;;;;;;Condoms;Condom promotion and distribution;Prevention;M.condom.reg[:];M.condom.cas[:];;Condom use proportion for regular sexual acts;All;Condom use proportion for casual sexual acts;All;;;;;;;;;;;;;;;SBCC;Social and behavior change communication;Prevention;M.condom.reg[:];M.condom.cas[:];;Condom use proportion for regular sexual acts;All;Condom use proportion for casual sexual acts;All;;;;;;;;;;;;;;;STI;Diagnosis and treatment of sexually transmissible infections;Prevention;M.stiprevulc[:];;;Ulcerative STI prevalence;All;;;;;;;;;;;;;;;;;VMMC;Voluntary medical male circumcision;Prevention;M.numcircum[:];;;Number of medical male circumcisions performed per year;All;;;;;;;;;;;;;;;;;FSW programs;Programs for female sex workers and clients;Prevention;M.condom.com[FSW];M.condom.com[Clients];M.hivtest[FSW];Condom use proportion for commercial sexual acts;FSW;Condom use proportion for commercial sexual acts;Clients;Proportion of people who are tested for HIV each year;FSW;;;;;;;;;;;;;MSM programs;Programs for men who have sex with men;Prevention;M.condom.reg[MSM];M.condom.cas[MSM];;Condom use proportion for regular sexual acts;MSM;Condom use proportion for casual sexual acts;MSM;;;;;;;;;;;;;;;PWID programs;Programs for people who inject drugs;Prevention;M.hivtest[PWID];M.condom.reg[PWID];M.condom.cas[PWID];Proportion of people who are tested for HIV each year;PWID;Condom use proportion for regular sexual acts;PWID;Number of casual sexual acts per person per year;PWID;;;;;;;;;;;;;OST;Opiate substitution therapy;Prevention;M.numost;;;Number of people on OST;All;;;;;;;;;;;;;;;;;NSP;Needle-syringe program;Prevention;M.sharing[:];;;Proportion of injections using receptively shared needle-syringes;All;;;;;;;;;;;;;;;;;PrEP;Pre-exposure prophylaxis;Prevention;M.prep[:];;;Proportion of risk encounters covered by PrEP;All;;;;;;;;;;;;;;;;;Cash transfers;Cash transfers for HIV risk reduction;Prevention;M.numacts.reg[:];M.numacts.cas[:];;Number of regular sexual acts per person per year;All;Number of casual sexual acts per person per year;All;;;;;;;;;;;;;;;HTC;HIV testing and counseling;Care and treatment;M.hivtest[:];;;HIV testing rates;All;;;;;;;;;;;;;;;;;ART;Antiretroviral therapy;Care and treatment;M.txtotal;;;Number of PLHIV on ART;All;;;;;;;;;;;;;;;;;PMTCT;Prevention of mother-to-child transmission;Care and treatment;M.numpmtct;;;Number of pregnant women receiving Option B/B+;All;;;;;;;;;;;;;;;;;PEP;Post-exposure prophylaxis;Care and treatment;;;;;;;;;;;;;;;;;;;;;;OVC;Orphans and vulnerable children;Care and treatment;;;;;;;;;;;;;;;;;;;;;;Other care;Other care;Care and treatment;;;;;;;;;;;;;;;;;;;;;;MGMT;Management;Management/administration;;;;;;;;;;;;;;;;;;;;;;HR;HR and training;Management/administration;;;;;;;;;;;;;;;;;;;;;;ENV;Enabling environment;Management/administration;;;;;;;;;;;;;;;;;;;;;;SP;Social protection;Other;;;;;;;;;;;;;;;;;;;;;;M&E;Monitoring, evaluation, surveillance, and research;Other;;;;;;;;;;;;;;;;;;;;;;INFR;Health infrastructure;Other;;;;;;;;;;;;;;;;;;;;;;Other;Other costs;Other;;;;;;;;;;;;;;;;;;;;;;"""fields = {0:"short_name",1:"name",2:"category"}param_cols = [3,4,5]def programs():    #TODO cleanup pops when no limitation for populations is in place    import re    from parameters import maybe_bool    result = []    lines = [l.strip() for l in ALL_PROGRAMS_SOURCE.split('\n')][2:-1]    split_lines = [l.split(';') for l in lines]    for line in split_lines:        entry = dict([(fields[key], maybe_bool(line[key]) ) for key in fields])        params = []        for col in param_cols:            if line[col]:                param, pops = re.match('M\.([^[]+)(?:\[(.+?)\])?',line[col]).groups()                if pops is None: pops=''                params.append({'signature': param.split('.'), 'pops':pops.replace(':','').split(',')})        entry['parameters'] = params        result.append(entry)    return resultprogram_list = programs()def programs_for_input_key(key): #params is the output of parameters.parameters() method    from parameters import input_parameter    param = input_parameter(key)    result = {}    keys = None    if param is not None: keys = param.get('keys')    if keys is not None:        for program in program_list:            program_name = program['short_name']            for parameter in program['parameters']:                if parameter['signature']==keys:                    if program_name not in result:                        result[program_name] = []                    pops = parameter['pops']                    if pops and pops!=['']:                        result[program_name].extend(pops)    return resultdef program_categories():    result = []    next_category = None    for p in program_list:        current_category = p['category']        if next_category is not None and next_category['category']==current_category:            next_category['programs'].append({'short_name':p['short_name'], 'name':p['name']})        else:            if next_category is not None: result.append(next_category)            next_category = {'category':current_category}            next_category['programs'] = []    if next_category is not None: result.append(next_category)    return result