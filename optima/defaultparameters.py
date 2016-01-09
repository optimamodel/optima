# -*- coding: utf-8 -*-
"""
Created on Sat Jan  9 10:24:09 2016

@author: robynstuart
"""

long_names = [
'Condoms | Proportion of sexual acts in which condoms are used with commercial partners',
'Condoms | Proportion of sexual acts in which condoms are used with casual partners',
'Condoms | Proportion of sexual acts in which condoms are used with regular partners',
'Acts | Number of sexual acts per person per year with commercial partners',
'Acts | Number of sexual acts per person per year with casual partners',
'Acts | Number of sexual acts per person per year with regular partners',
'Circumcision | Proportion of males who are circumcised',
'Circumcision | Number of medical male circumcisions performed per year',
'STI | Prevalence of  STIs',
'Testing | Proportion of people who are tested for HIV each year',
'Treatment | Number of PLHIV on ART',
'PrEP | Proportion of risk encounters covered by PrEP',
'Injecting drug use | Number of injections per person per year',
'Injecting drug use | Proportion of injections using receptively shared needle-syringes',
'Injecting drug use | Number of people on OST',
'PMTCT | Number of pregnant women receiving Option B/B+',
'PMTCT | Proportion of mothers who breastfeed']

targetpartypes = [
'condcom',
'condcas',
'condreg',
'actscom',
'actscas',
'actsreg',
'circum',
'numcircum',
'stiprev',
'hivtest',
'numtx',
'prep',
'actsinj',
'sharing',
'numost',
'numpmtct',
'breast'
]

coveragepar = [
0,
0,
0,
0,
0,
0,
0,
1,
0,
0,
1,
0,
0,
0,
1,
1,
0
]



by_population = [
1,
1,
1,
1,
1,
1,
1,
1,
1,
1,
0,
1,
1,
1,
0,
0,
0
]

textfield1 = [
'Condom usage for persons not covered by any program:',
'Condom usage for persons not covered by any program:',
'Condom usage for persons not covered by any program:',
'Average number of acts for persons not covered by any program:',
'Average number of acts for persons not covered by any program:',
'Average number of acts for persons not covered by any program:',
'Prevalence of circumcision in the absence of any program:',
'Number of circumcisions performed outside of any program:',
'STI prevalence for a person not covered by any program:',
'HIV testing rate for a person not covered by any program:',
'Number of PLHIV accessing treatment in the absence of any program:',
'Proportion of risk encounters covered by PrEP for a person not covered by any program:',
'Average number of injections for a person not covered by any program:',
'Average sharing rate for a person not covered by any program:',
'Number of people accessing OST in the absence of any program:',
'Number of PLHIV accessing PMTCT in the absence of any program:',
'Average breastfeeding rate for PLHIV not covered by any program:'
]

textfield2 = [
'Condom usage for persons covered by this program only:',
'Condom usage for persons covered by this program only:',
'Condom usage for persons covered by this program only:',
'Average number of acts for persons covered by this program only:',
'Average number of acts for persons covered by this program only:',
'Average number of acts for persons covered by this program only:',
'',
'',
'STI prevalence among persons covered by this program only:',
'HIV testing rates among persons covered by this program only:',
'',
'Proportion of risk encounters covered by PrEP for a person covered by this program only:',
'Average number of injections for a person covered by this program only:',
'Average sharing rate for a person covered by this program only:',
'',
'',
''
]


default_interactions = [
'random',
'random',
'random',
'random',
'random',
'random',
None,
None,
'random',
'random',
None,
'random',
'random',
'random',
None,
None,
'random'
]

parameter_type = [
'condcom',
'condcas',
'condreg',
'actscom',
'actscas',
'actsreg',
'circum',
'numcircum',
'stiprev',
'hivtest',
'numtx',
'prep',
'actsinj',
'sharing',
'numost',
'numpmtct',
'breast'
]