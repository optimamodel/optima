"""
90-90-90 scenario for Optima
"""

from optima import Parscen, defaults, pygui, plotpeople

P = defaults.defaultproject('simple')
P.settings.usecascade = True
P.runsim()

pops = P.data['pops']['short']

## Define scenarios
scenlist = [
    Parscen(name='Current conditions',
            parsetname='default',
            pars=[]),

     Parscen(name='90-90-90',
          parsetname='default',
          pars=[
          {'name': 'propdx',
          'for': ['tot'],
          'startyear': 2016,
          'endyear': 2020,
          'startval': .5,
          'endval': .9,
          },
          
          {'name': 'propcare',
          'for': ['tot'],
          'startyear': 2016,
          'endyear': 2020,
          'startval': .5,
          'endval': .9,
          },
          
          {'name': 'proptx',
          'for': ['tot'],
          'startyear': 2016,
          'endyear': 2020,
          'startval': .5,
          'endval': .9,
          },
          
          {'name': 'treatvs',
          'for': ['tot'],
          'startyear': 2016,
          'endyear': 2020,
          'startval': .5,
          'endval': .9,
          },
            ]),
    ]

# Store these in the project
P.addscenlist(scenlist)

# Run the scenarios
P.runscenarios() 
 
ppl = P.results[-1].raw['90-90-90'][0]['people']
plotpeople(P, ppl)
pygui(P.results[-1], toplot='cascade')

