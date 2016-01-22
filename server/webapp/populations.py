ALL_POPULATIONS_SOURCE = \
"""
Short name;Full name;Male;Female;AgeFrom;AgeTo
FSW;Female sex workers;0;1;15;49;
Clients;Clients of sex workers;1;0;15;49;
MSM;Men who have sex with men;1;0;15;49;
Transgender;Transgender individuals;0;0;15;49;
PWID;People who inject drugs;0;0;15;49;
Male PWID;Males who inject drugs;1;0;15;49;
Female PWID;Females who inject drugs;0;1;15;49;
Children;Children;0;0;2;15;
Infants;Infants;0;0;0;2;
Males;Other males;1;0;15;49;
Females;Other females;0;1;0;15;49;
Other males;Other males [enter age];1;0;0;0;
Other females;Other females [enter age];0;1;0;0;
"""

## TODO Cliff, Robyn: are these populations still going to be used or not?
## we need this to show populations list in Create Project screen

fields = {0:"short_name",1:"name", 2:"male", 3:"female",4:"age_from",5:"age_to"}

def populations():
    from parameters import maybe_bool
    lines = [l.strip() for l in ALL_POPULATIONS_SOURCE.split('\n')][2:-1]
    split_lines = [l.split(';') for l in lines]
    return [dict([(fields[key], maybe_bool(line[key]) ) for key in fields]) for line in split_lines]


def project_population_data():
    pops = populations()
    return {
        'short': [pop['short_name'] for pop in pops],
        'male': [pop['male'] for pop in pops],
        'female': [pop['female'] for pop in pops],
    }


def population_keys():
    return [pop['short_name'] for pop in populations()]

