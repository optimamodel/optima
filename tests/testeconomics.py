# -*- coding: utf-8 -*-
"""
Created on Sun Jan 17 19:22:29 2016

@author: robynstuart
"""
from optima import Settings, Project, runmodel
from optima.loadeconomicsspreadsheet import loadeconomicsspreadsheet, makeecontimeseries, getartcosts

# Read in economic data
econdata = loadeconomicsspreadsheet('testeconomics.xlsx') 

# Make a time vector
settings = Settings()
start = settings.start
end = settings.end + 50
dt = settings.dt
from numpy import linspace
tvec = linspace(start, end, round((end-start)/dt)+1)

# Make interpolated/extrapolated economic time series
econtimeseries = makeecontimeseries(econdata, tvec)

# Make interpolated/extrapolated economic time series
from optima.defaultprograms import defaultprogset
P = Project(spreadsheet='test7pops.xlsx')
R = defaultprogset(P, addpars=True, addcostcov=True, filterprograms=['Condoms', 'FSW_programs', 'MSM_programs', 'HTC', 'ART', 'PMTCT', 'MGMT', 'HR', 'Other'])

artunitcosts = getartcosts(R, tvec, shortnameofART='ART', growthrateofARTcost=0.0)

cd4costs = econtimeseries['socialcosts'] + econtimeseries['healthcosts']

results = runmodel(pars=P.parsets['default'].pars[0])

plhiv = {}
for j in range(settings.ncd4):
    plhiv[settings.hivstates[j]] = results.raw[0]['people'][settings.__dict__[settings.hivstates[j]],:,:].sum(axis=(0,1))


# Create some plots
from pylab import figure, plot, hold, scatter
figure()
hold(True)
plot(tvec, econtimeseries['cpi'][0])
scatter(econdata['years'],econdata['cpi']['past'][0])

figure()
hold(True)
plot(tvec, econtimeseries['gdp'][0])
scatter(econdata['years'],econdata['gdp']['past'][0])

figure()
hold(True)
plot(tvec, econtimeseries['govrev'][0])
scatter(econdata['years'],econdata['govrev']['past'][0])

figure()
hold(True)
plot(tvec, econtimeseries['govexp'][0])
scatter(econdata['years'],econdata['govexp']['past'][0])

figure()
hold(True)
plot(tvec, econtimeseries['totexp'][0])
scatter(econdata['years'],econdata['totexp']['past'][0])

figure()
hold(True)
plot(tvec, econtimeseries['govhealth'][0])
scatter(econdata['years'],econdata['govhealth']['past'][0])

figure()
hold(True)
plot(tvec, econtimeseries['healthcosts'][5])
scatter(econdata['years'],econdata['healthcosts']['past'][5])

figure()
hold(True)
plot(tvec, artunitcosts)
scatter(array(R.programs['ART'].costcovfn.ccopars['t']),array(R.programs['ART'].costcovfn.getccopar(R.programs['ART'].costcovfn.ccopars['t'])['unitcost']))
