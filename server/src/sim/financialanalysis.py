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

default_costdisplay = 'total' # will come from FE, and be one of ['total','gdp','revenue','govtexpend','totalhealth','domestichealth']

def financialanalysis(D, postyear=2015, S=None, costdisplay=default_costdisplay, makeplot=False):
    '''
    Plot financial commitment graphs
    '''
    
    # If not supplied as input, copy from D
    if not(isinstance(S,dict)): S = D.S

    # Initialise some things
    costs = {}
    costsbase = {}
    costszero = {}
    socialcosts = {}
    othercosts = {}
    postyear = float(postyear)

    # Get y axis scaling factor
    yscalefactor = costdisplay if not costdisplay=='total' else 0

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
        if yscalefactor:
            yscale = sanitize(D.data.econ[yscalefactor])
            if isinstance(yscale,int): raise Exception('No data have been provided for this varaible, so we cannot display the costs as a proportion of this')

        # Interpolating
        newx = linspace(0,1,ndatapts)
        origx = linspace(0,1,len(socialcosts[healthstate]))
        socialcosts[healthstate] = smoothinterp(newx, origx, socialcosts[healthstate], smoothness=5)
        origx = linspace(0,1,len(othercosts[healthstate]))
        othercosts[healthstate] = smoothinterp(newx, origx, othercosts[healthstate], smoothness=5)
        if yscalefactor:
            origx = linspace(0,1,len(yscale))
            yscale = smoothinterp(newx, origx, yscale, smoothness=5)
            yscale = append(yscale,[yscale[-1]]*(noptpts-ndatapts))

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
            
    # Set y axis scale and set y axis to the right time period
    xdata = opttvec

    if not yscalefactor:
        ydata1 = annualhivcostsbase
        ydata2 = cumulhivcostsbase
        ydata3 = annualhivcostszero
        ydata4 = cumulhivcostszero
    else:
        ydata1 = [annualhivcostsbase[j] / yscale[j] for j in range(noptpts)]
        ydata2 = cumulhivcostsbase
        ydata3 = [annualhivcostszero[j] / yscale[j] for j in range(noptpts)]
        ydata4 = cumulhivcostszero

    # Store results
    plotdata = {}
    plotdata['annualhivcosts'] = {}
    plotdata['annualhivcosts']['xlinedata'] = xdata
    plotdata['annualhivcosts']['ylinedata'] = ydata1
    plotdata['annualhivcosts']['title'] = 'Total HIV-related financial commitments - annual'
    plotdata['annualhivcosts']['xlabel'] = 'Year'
    plotdata['annualhivcosts']['ylabel'] = 'USD'
    
    plotdata['cumulhivcosts'] = {}
    plotdata['cumulhivcosts']['xlinedata'] = xdata
    plotdata['cumulhivcosts']['ylinedata'] = ydata2 
    plotdata['cumulhivcosts']['title'] = 'Total HIV-related financial commitments - cumulative'
    plotdata['cumulhivcosts']['xlabel'] = 'Year'
    plotdata['cumulhivcosts']['ylabel'] = 'USD'

    plotdata['annualhivcostsfuture'] = {}
    plotdata['annualhivcostsfuture']['xlinedata'] = xdata
    plotdata['annualhivcostsfuture']['ylinedata'] = ydata3
    plotdata['annualhivcostsfuture']['title'] = 'Financial commitments for existing PLHIV - annual'
    plotdata['annualhivcostsfuture']['xlabel'] = 'Year'
    plotdata['annualhivcostsfuture']['ylabel'] = 'USD'

    plotdata['cumulhivcostsfuture'] = {}
    plotdata['cumulhivcostsfuture']['xlinedata'] = xdata
    plotdata['cumulhivcostsfuture']['ylinedata'] = ydata4
    plotdata['cumulhivcostsfuture']['title'] = 'Financial commitments for existing PLHIV - cumulative'
    plotdata['cumulhivcostsfuture']['xlabel'] = 'Year'
    plotdata['cumulhivcostsfuture']['ylabel'] = 'USD'

    if makeplot:
        from matplotlib.pylab import figure, plot, hold, xlabel, ylabel, title #we don't need it for the whole module in web context

        figure()
        hold(True)
        plot(plotdata['annualhivcosts']['xlinedata'], plotdata['annualhivcosts']['ylinedata'], lw = 2, c = 'b')
        plot(plotdata['annualhivcostsfuture']['xlinedata'], plotdata['annualhivcostsfuture']['ylinedata'], lw = 2, c = 'r')
        title(plotdata['annualhivcosts']['title'])
        xlabel('Year')
        ylabel('USD')

        figure()
        hold(True)
        plot(plotdata['cumulhivcosts']['xlinedata'], plotdata['cumulhivcosts']['ylinedata'], lw = 2, c = 'b')
        plot(plotdata['cumulhivcostsfuture']['xlinedata'], plotdata['cumulhivcostsfuture']['ylinedata'], lw = 2, c = 'r')
        title(plotdata['cumulhivcosts']['title'])
        xlabel('Year')
        ylabel('USD')
        
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
plotdata = financialanalysis(D, postyear=2015, S=D.S, costdisplay=default_costdisplay, makeplot=1)
