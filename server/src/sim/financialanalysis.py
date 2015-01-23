"""
Created on Sat Nov 29 17:40:34 2014

@author: robynstuart
"""
from numpy import linspace, arange, append
import copy
from setoptions import setoptions
from copy import deepcopy
from utils import sanitize
from utils import smoothinterp

#default_costdisplay = 'revenue' # will come from FE, and be one of ['total','gdp','revenue','govtexpend','totalhealth','domestichealth']

def financialanalysis(D, postyear=2015, S=None, makeplot=False):
    '''
    Plot financial commitment graphs
    '''
    
    # If not supplied as input, copy from D
    if not(isinstance(S,dict)): S = D.S

    # Initialise some things
    plotdata = {}
    plotdata['annualhivcostsexisting'] = {}
    plotdata['annualhivcostsfuture'] = {}
    plotdata['annualhivcoststotal'] = {}
    costs = {}
    costsbase = {}
    costszero = {}
    socialcosts = {}
    othercosts = {}
    postyear = float(postyear)
    costdisplays = ['total','gdp','revenue','govtexpend','totalhealth','domestichealth']

#    # Get y axis scaling factor
#    yscalefactor = costdisplay if not costdisplay=='total' else 0

    # Set up variables for time indexing
    datatvec = arange(D.G.datastart, D.G.dataend+D.opt.dt, D.opt.dt)
    ndatapts = len(datatvec)
    opttvec = D.opt.tvec
    noptpts = D.opt.npts

    # Get most recent ART unit costs
    progname = 'ART'
    prognumber = D.data.meta.progs.short.index(progname)
    artunitcost = sanitize([D.data.costcov.cost[prognumber][j]/D.data.costcov.cov[prognumber][j] for j in range(len(D.data.costcov.cov[prognumber]))])[-1]

    # Run a simulation with the force of infection set to zero from postyear... 
    opt = setoptions(startyear=D.opt.startyear, endyear=D.opt.endyear, nsims=1, turnofftrans=postyear)
    from model import model
    S0 = model(D.G, D.M, D.F[0], opt, initstate=None)

    # Extract the number of PLHIV under the baseline sim and the zero transmission sim
    peoplebase = S.people[:,:,:]
    peoplezero = S0.people[:,:,:]
    totalcostsbase = [0.0]*noptpts
    totalcostszero = [0.0]*noptpts
    
    # Interpolate costs & economic indicators
    for healthno, healthstate in enumerate(D.G.healthstates):

        # Remove NaNs from data
        socialcosts[healthstate] = sanitize(D.data.econ.social[healthno])
        othercosts[healthstate] = sanitize(D.data.econ.health[healthno])

        # Interpolating
        newx = linspace(0,1,ndatapts)
        origx = linspace(0,1,len(socialcosts[healthstate]))
        socialcosts[healthstate] = smoothinterp(newx, origx, socialcosts[healthstate], smoothness=5)
        origx = linspace(0,1,len(othercosts[healthstate]))
        othercosts[healthstate] = smoothinterp(newx, origx, othercosts[healthstate], smoothness=5)

        # Extrapolating... holding constant for now. #TODO use growth rates when they have been added to the excel sheet
        othercosts[healthstate] = append(othercosts[healthstate],[othercosts[healthstate][-1]]*(noptpts-ndatapts))
        socialcosts[healthstate] = append(socialcosts[healthstate],[socialcosts[healthstate][-1]]*(noptpts-ndatapts))
        costs[healthstate] = [(socialcosts[healthstate][j] + othercosts[healthstate][j]) for j in range(noptpts)]

        # Calculate annual non-treatment costs for all PLHIV under the baseline sim and the zero transmission sim
        costsbase[healthstate] = [peoplebase[D.G[healthstate],:,j].sum(axis = (0,1))*costs[healthstate][j] for j in range(noptpts)]
        costszero[healthstate] = [peoplezero[D.G[healthstate],:,j].sum(axis = (0,1))*costs[healthstate][j] for j in range(noptpts)]
        
        totalcostsbase = [totalcostsbase[j] + costsbase[healthstate][j] for j in range(noptpts)]
        totalcostszero = [totalcostszero[j] + costszero[healthstate][j] for j in range(noptpts)]

    # Calculate annual treatment costs for PLHIV
    ### TODO: discounting!! ###
    tx1base = peoplebase[D.G.tx1[0]:D.G.fail[-1],:,:].sum(axis=(0,1))
    tx2base = peoplebase[D.G.tx2[0]:D.G.tx2[-1],:,:].sum(axis=(0,1))
    onartbase = [tx1base[j] + tx2base[j] for j in range(noptpts)]
    artcostbase = [onartbase[j]*artunitcost for j in range(noptpts)]
    
    # Calculate annual treatment costs for new PLHIV
    tx1zero = peoplezero[D.G.tx1[0]:D.G.fail[-1],:,:].sum(axis=(0,1))
    tx2zero = peoplezero[D.G.tx2[0]:D.G.tx2[-1],:,:].sum(axis=(0,1))
    onartzero = [tx1zero[j] + tx2zero[j] for j in range(noptpts)]
    artcostzero = [onartzero[j]*artunitcost for j in range(noptpts)]

    # Calculate annual total costs for all and new PLHIV
    annualhivcostsbase = [totalcostsbase[j] + artcostbase[j] for j in range(noptpts)]
    annualhivcostszero = [totalcostszero[j] + artcostzero[j] for j in range(noptpts)]
    annualhivcostsfuture = [annualhivcostsbase[j] - annualhivcostszero[j] for j in range(noptpts)]

    # Cumulative sum function (b/c can't find an inbuilt one)
    def accumu(lis):
        total = 0
        for x in lis:
            total += x
            yield total

    # Calculate cumulative total costs for PLHIV
    cumulhivcostsbase = list(accumu(annualhivcostsbase))
    cumulhivcostszero = list(accumu(annualhivcostszero))
    cumulhivcostsfuture = list(accumu(annualhivcostsfuture))
            
    xdata = opttvec

    # Set y axis scale and set y axis to the right time period
    for yscalefactor in costdisplays:
        
        plotdata['annualhivcostsexisting'][yscalefactor] = {}
        plotdata['annualhivcostsfuture'][yscalefactor] = {}
        plotdata['annualhivcoststotal'][yscalefactor] = {}

        plotdata['annualhivcostsexisting'][yscalefactor]['xlinedata'] = xdata
        plotdata['annualhivcostsfuture'][yscalefactor]['xlinedata'] = xdata
        plotdata['annualhivcoststotal'][yscalefactor]['xlinedata'] = xdata

        plotdata['annualhivcostsexisting'][yscalefactor]['xlabel'] = 'Year'
        plotdata['annualhivcostsfuture'][yscalefactor]['xlabel'] = 'Year'
        plotdata['annualhivcoststotal'][yscalefactor]['xlabel'] = 'Year'

        if yscalefactor=='total':
            plotdata['annualhivcostsexisting'][yscalefactor]['ylinedata'] = annualhivcostszero 
            plotdata['annualhivcostsfuture'][yscalefactor]['ylinedata'] = annualhivcostsfuture
            plotdata['annualhivcoststotal'][yscalefactor]['ylinedata'] = annualhivcostsbase

            plotdata['annualhivcostsexisting'][yscalefactor]['ylabel'] = 'Proportion of ' + yscalefactor
            plotdata['annualhivcostsfuture'][yscalefactor]['ylabel'] = 'Proportion of ' + yscalefactor
            plotdata['annualhivcoststotal'][yscalefactor]['ylabel'] = 'Proportion of ' + yscalefactor

            plotdata['annualhivcostsexisting'][yscalefactor]['title'] = 'Annual HIV-related financial commitments - existing infections'
            plotdata['annualhivcostsfuture'][yscalefactor]['title'] = 'Annual HIV-related financial commitments - post-2015 infections'
            plotdata['annualhivcoststotal'][yscalefactor]['title'] = 'Annual HIV-related financial commitments - all PLHIV'
        else:
            yscale = sanitize(D.data.econ[yscalefactor])
            if isinstance(yscale,int): continue #raise Exception('No data have been provided for this varaible, so we cannot display the costs as a proportion of this')
            origx = linspace(0,1,len(yscale))
            yscale = smoothinterp(newx, origx, yscale, smoothness=5)
            yscale = append(yscale,[yscale[-1]]*(noptpts-ndatapts))

            plotdata['annualhivcostsexisting'][yscalefactor]['ylinedata'] = [annualhivcostszero[j] / yscale[j] for j in range(noptpts)]
            plotdata['annualhivcostsfuture'][yscalefactor]['ylinedata'] = [annualhivcostsfuture[j] / yscale[j] for j in range(noptpts)]
            plotdata['annualhivcoststotal'][yscalefactor]['ylinedata'] = [annualhivcostsbase[j] / yscale[j] for j in range(noptpts)]

            plotdata['annualhivcostsexisting'][yscalefactor]['ylabel'] = 'Proportion of ' + yscalefactor
            plotdata['annualhivcostsfuture'][yscalefactor]['ylabel'] = 'Proportion of ' + yscalefactor
            plotdata['annualhivcoststotal'][yscalefactor]['ylabel'] = 'Proportion of ' + yscalefactor

            plotdata['annualhivcostsexisting'][yscalefactor]['title'] = 'Annual HIV-related financial commitments - existing infections'
            plotdata['annualhivcostsfuture'][yscalefactor]['title'] = 'Annual HIV-related financial commitments - post-2015 infections'
            plotdata['annualhivcoststotal'][yscalefactor]['title'] = 'Annual HIV-related financial commitments - all PLHIV'
    
    plotdata['cumulhivcostsexisting'] = {}
    plotdata['cumulhivcostsfuture'] = {}
    plotdata['cumulhivcoststotal'] = {}

    plotdata['cumulhivcostsexisting']['ylinedata'] = cumulhivcostszero
    plotdata['cumulhivcostsfuture']['ylinedata'] = cumulhivcostsfuture
    plotdata['cumulhivcoststotal']['ylinedata'] = cumulhivcostsbase

    plotdata['cumulhivcostsexisting']['ylabel'] = 'USD'
    plotdata['cumulhivcostsfuture']['ylabel'] = 'USD'
    plotdata['cumulhivcoststotal']['ylabel'] = 'USD'

    plotdata['cumulhivcostsexisting']['title'] = 'Cumulative HIV-related financial commitments - existing infections'
    plotdata['cumulhivcostsfuture']['title'] = 'Cumulative HIV-related financial commitments - post-2015 infections'
    plotdata['cumulhivcoststotal']['title'] = 'Cumulative HIV-related financial commitments - all PLHIV'

    plotdata['cumulhivcostsexisting']['xlinedata'] = xdata
    plotdata['cumulhivcostsfuture']['xlinedata'] = xdata
    plotdata['cumulhivcoststotal']['xlinedata'] = xdata

    plotdata['cumulhivcostsexisting']['xlabel'] = 'Year'
    plotdata['cumulhivcostsfuture']['xlabel'] = 'Year'
    plotdata['cumulhivcoststotal']['xlabel'] = 'Year'

    # Get financial commitments
    return plotdata


##############################################
# Helper functions
##############################################
def snipM(M, thisindex = range(150,301)):
    '''
    Cut M to cover a specified time index
    '''
    M0 = copy.copy(M)
    M0.condom = copy.copy(M.condom)
    M0.numacts = copy.copy(M.numacts)
    M0.totalacts = copy.copy(M.totalacts)
    
    # Loop over parameters in M and snip the time varying ones....
    for param in M0.keys():
        if param in ['transit','pships', 'const', 'hivprev']:
            continue
        elif param in ['condom', 'numacts']:
            for key in M0[param]:
                M0[param][key] = M0[param][key][:, thisindex]
        elif param in ['totalacts']:
            for key in M0[param]:
                M0[param][key] = M0[param][key][:, :, thisindex]
        elif np.ndim(M0[param])==1:
            M0[param] = M0[param][thisindex]
        elif np.ndim(M0[param])==2:
            M0[param] = M0[param][:, thisindex]
        else:
            raise Exception('Parameter type %s doesn''t fit into obvious cases' % param)

    return M0

#example
#plotdata = financialanalysis(D, postyear=2015, S=D.S, costdisplay=default_costdisplay, makeplot=1)
