"""
Make Optima HIV demo projects (used in web interface)
Created on Thu Sep 21 11:51:08 2017

"""

from optima import defaultproject, Parscen, Optim, defaultobjectives, odict

tomake = ['concentrated','generalized']
dorun = True

### Make projects
for proj in tomake:

    P = defaultproject(proj,dorun=False)
    P.copyparset('default','Treatment fixed')
    P.parsets['Treatment fixed'].fixprops(False)
    P.copyparset('default','Status quo')
    P.rmparset('default')
    
    
    ### Scenarios
    P.scens = odict()
    P.addscens([Parscen(name='Status quo',parsetname='Status quo',pars=[]),
                Parscen(name='90-90-90/95-95-95',parsetname='Treatment fixed',
                        pars=[{'name': 'propdx', 'startyear': 2015.0, 'for': 'tot', 'endval': 0.9, 'endyear': 2020.0,},
                              {'name': 'propdx', 'startyear': 2020.0, 'for': 'tot', 'endval': 0.95, 'endyear': 2030.0, 'startval': 0.9},
                              {'name': 'propcare', 'startyear': 2015.0, 'startval': 1.0, 'for': 'tot'},
                              {'name': 'proptx', 'startyear': 2015.0, 'endval': 0.9, 'endyear': 2020.0, 'for': 'tot'}, 
                              {'name': 'proptx', 'startyear': 2020.0, 'for': 'tot', 'endval': 0.95, 'endyear': 2030, 'startval': 0.9},
                              {'name': 'propsupp', 'startyear': 2015.0, 'endval': 0.9, 'endyear': 2020.0, 'for': 'tot'},
                              {'name': 'propsupp', 'startyear': 2020.0, 'for': 'tot', 'endval': 0.95, 'endyear': 2030.0, 'startval': 0.9}]),
                    ])


    ### Optimizations
    P.optims = odict()
    optim = Optim(project=P, parsetname='Treatment fixed', name='Optimal with latest reported funding')
    P.addoptim(optim)
    
    objectives = defaultobjectives(P, which='money')
    optim = Optim(project=P, parsetname='Treatment fixed', name='Minimal funding to reduce incidence and deaths by 25%', objectives=objectives)
    P.addoptim(optim)


    ### Save project
    P.save(filename=P.name+'.prj')


