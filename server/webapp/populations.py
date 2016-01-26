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
""" # WARNING, this should probably not be hard-coded here

fields = {0:"short_name",1:"name", 2:"male", 3:"female",4:"age_from",5:"age_to",6:"injects",7:"sexworker"}

def maybe_bool(p):
    ''' A function that returns a Boolean value if the input is a string '0' or '1', else returns the original string '''
    if p in ['0','1']: return bool(int(p))
    else: return p
    return p

def populations():
    lines = [l.strip() for l in ALL_POPULATIONS_SOURCE.split('\n')][2:-1]
    split_lines = [l.split(';') for l in lines]
    return [dict([(fields[key], maybe_bool(line[key])) for key in fields]) for line in split_lines]


def project_population_data():
    pops = populations()
    return {
        'short': [pop['short_name'] for pop in pops],
        'male': [pop['male'] for pop in pops],
        'female': [pop['female'] for pop in pops],
        'injects': [pop['injects'] for pop in pops],
        'sexworker': [pop['sexworker'] for pop in pops],
    }


def population_keys():
    return [pop['short_name'] for pop in populations()]

