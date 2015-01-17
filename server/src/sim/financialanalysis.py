"""
Created on Sat Nov 29 17:40:34 2014

@author: robynstuart
"""
import numpy as np
import copy
from setoptions import setoptions
from copy import deepcopy

def financialanalysis(D, postyear = 2015, S = None, yscale = 'abs', makeplot = False):
    '''
    Plot financial commitment graphs
    Note, yscale will be chosen from ['abs', 'avg', 'avgppp']
    '''
    
    # If not supplied as input, copy from D
    if not(isinstance(S,dict)): S = D.S
    
    # Interpolate macroeconomic indicators 
    if not yscale == 'abs':
        ydenom = []
        for i in range(len(D.data.macro[yscale][0])-1):
            ydenom.extend(np.linspace(D.data.macro[yscale][0][i],D.data.macro[yscale][0][i+1],10,endpoint = False).tolist())
        ydenom.append(D.data.macro[yscale][0][-1])
        ydenom = [ydenom[j] for j in range(len(ydenom))]

    # Get future time index
    opt = setoptions(startyear=postyear, endyear=D.opt.endyear, nsims=1)
    futureindex = np.where(D.opt.tvec - opt.tvec[0]>-0.01)[0]

    # Get indices for the different disease states # TODO these should be defined globally somewhere... 
    print('Warning, missing CD4>50')
    acute, gt500, gt350, gt200, aids = D.G.acute, D.G.gt500, D.G.gt350, D.G.gt200, D.G.aids

    # Set force of infection to zero... 
    zeroF = deepcopy(D.F[0])
    zeroF.force = D.G.npops*[0.] # TODO -- find out why F is turning into a list from an array
    initstate = S.people[:,:,futureindex[0]]
    
    # Extract the number of PLHIV under the baseline sim
    peoplebase = S.people[:,:,:]

    # Calculate total number in each disease stage under baseline sim
    acuteplhivbase = np.sum(peoplebase[acute,:,:], axis = (0,1))
    gt500plhivbase = np.sum(peoplebase[gt500,:,:], axis = (0,1))
    gt350plhivbase = np.sum(peoplebase[gt350,:,:], axis = (0,1))
    gt200plhivbase = np.sum(peoplebase[gt200,:,:], axis = (0,1))
    aidsplhivbase = np.sum(peoplebase[aids,:,:], axis = (0,1))
    
    # Run a simulation with the force of infection set to zero from postyear... 
    from model import model
    M0 = snipM(D.M, futureindex.tolist())
    S0 = model(D.G, M0, zeroF, opt, initstate)

    # Extract the number of PLHIV under the zero transmission sim
    peoplezero = S0.people[:,:,:]
    peoplezero = np.concatenate((peoplebase[:,:,0:futureindex[0]], peoplezero), axis=2)

    # Calculate total number in each disease stage under the zero transmission sim
    acuteplhivzero = np.sum(peoplezero[acute,:,:], axis = (0,1))
    gt500plhivzero = np.sum(peoplezero[gt500,:,:], axis = (0,1))
    gt350plhivzero = np.sum(peoplezero[gt350,:,:], axis = (0,1))
    gt200plhivzero = np.sum(peoplezero[gt200,:,:], axis = (0,1)) 
    aidsplhivzero = np.sum(peoplezero[aids,:,:], axis = (0,1))

    # Interpolate time for plotting
    xdata = D.opt.tvec
    npts = D.opt.npts

    # Get most recent ART unit costs
    progname = 'ART'
    prognumber = D.data.meta.progs.short.index(progname)
    artunitcost = D.data.costcov.cost[prognumber]
    artunitcost = np.asarray(artunitcost)
    artunitcost = artunitcost[~np.isnan(artunitcost)]
    artunitcost = artunitcost[-1]
    
    #ATTN TODO CK -proper- way to read these data from econ (they used to be constants, not any more)
    econ_keys = ['acute','gt500','gt350', 'gt200', 'gt50','lt50'] # example.xlsx atm!

    # Calculate annual non-treatment costs for all PLHIV under the baseline sim
    acutecostbase = [D.data.econ.social[0][0]*acuteplhivbase[j] for j in range(npts)]
    gt500costbase = [D.data.econ.social[1][0]*gt500plhivbase[j] for j in range(npts)]
    gt350costbase = [D.data.econ.social[2][0]*gt350plhivbase[j] for j in range(npts)]
    gt200costbase = [D.data.econ.social[3][0]*gt200plhivbase[j] for j in range(npts)]
    aidscostbase = [D.data.econ.social[4][0]*aidsplhivbase[j] for j in range(npts)]

    # Calculate annual non-treatment costs for all PLHIV under the zero transmission sim
    acutecostzero = [D.data.econ.social[0][0]*acuteplhivzero[j] for j in range(npts)]
    gt500costzero = [D.data.econ.social[1][0]*gt500plhivzero[j] for j in range(npts)]
    gt350costzero = [D.data.econ.social[2][0]*gt350plhivzero[j] for j in range(npts)]
    gt200costzero = [D.data.econ.social[3][0]*gt200plhivzero[j] for j in range(npts)]
    aidscostzero = [D.data.econ.social[4][0]*aidsplhivzero[j] for j in range(npts)]

    # Calculate annual treatment costs for PLHIV
    ### TODO: discounting!! ###
    tx1base = peoplebase[D.G.tx1[0]:D.G.fail[-1],:,:].sum(axis=(0,1))
    tx2base = peoplebase[D.G.tx2[0]:D.G.tx2[-1],:,:].sum(axis=(0,1))
    onartbase = [tx1base[j] + tx2base[j] for j in range(npts)]
    artcostbase = [onartbase[j]*artunitcost for j in range(npts)]
    
    # Calculate annual treatment costs for new PLHIV
    tx1zero = peoplezero[D.G.tx1[0]:D.G.fail[-1],:,:].sum(axis=(0,1))
    tx2zero = peoplezero[D.G.tx2[0]:D.G.tx2[-1],:,:].sum(axis=(0,1))
    onartzero = [tx1zero[j] + tx2zero[j] for j in range(npts)]
    artcostzero = [onartzero[j]*artunitcost for j in range(npts)]

    # Calculate annual total costs for all and new PLHIV
    annualhivcostsbase = [acutecostbase[j] + gt500costbase[j] + gt350costbase[j] + gt200costbase[j] + aidscostbase[j] + artcostbase[j] for j in range(npts)]
    annualhivcostszero = [acutecostzero[j] + gt500costzero[j] + gt350costzero[j] + gt200costzero[j] + aidscostzero[j] + artcostzero[j] for j in range(npts)]
    annualhivcostsfuture = [annualhivcostsbase[j] - annualhivcostszero[j] for j in range(npts)]

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
    if yscale == 'abs':
        ydata1 = annualhivcostsbase
        ydata2 = cumulhivcostsbase
        ydata3 = annualhivcostszero
        ydata4 = cumulhivcostszero
    else:
        ydata1 = [annualhivcostsbase[j] / ydenom[j] for j in range(npts)]
        ydata2 = [cumulhivcostsbase[j] / ydenom[j] for j in range(npts)]
        ydata3 = [annualhivcostsfuture[j] / ydenom[j] for j in range(npts)]
        ydata4 = [cumulhivcostsfuture[j] / ydenom[j] for j in range(npts)]

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
        plot(acutecostbase, lw = 2, c = 'b')
        plot(acutecostzero, lw = 2, c = 'r')
        title('Acute costs')

        figure()
        hold(True)
        plot(gt500costbase, lw = 2, c = 'b')
        plot(gt500costzero, lw = 2, c = 'r')
        title('gt500 costs')

        figure()
        hold(True)
        plot(gt350costbase, lw = 2, c = 'b')
        plot(gt350costzero, lw = 2, c = 'r')
        title('gt350 costs')

        figure()
        hold(True)
        plot(gt200costbase, lw = 2, c = 'b')
        plot(gt200costzero, lw = 2, c = 'r')
        title('gt200 costs')

        figure()
        hold(True)
        plot(aidscostbase, lw = 2, c = 'b')
        plot(aidscostzero, lw = 2, c = 'r')
        title('aids costs')

        figure()
        hold(True)
        plot(artcostbase, lw = 2, c = 'b')
        plot(artcostzero, lw = 2, c = 'r')
        title('ART costs')

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
            M0[param].cas = M0[param].cas[:, thisindex]
            M0[param].reg = M0[param].reg[:, thisindex]
            M0[param].com = M0[param].com[:, thisindex]
            if param in ['numacts']:
                M0[param].inj = M0[param].inj[:, thisindex]
        elif param in ['totalacts']:
            M0[param].cas = M0[param].cas[:, :, thisindex]
            M0[param].reg = M0[param].reg[:, :, thisindex]
            M0[param].com = M0[param].com[:, :, thisindex]
            M0[param].inj = M0[param].inj[:, :, thisindex]
        elif param in ['aidstest', 'sharing', 'numpmtct', 'breast', 'tx1', 'tx2', 'numost']:
            M0[param] = M0[param][thisindex]
        else:
            M0[param] = M0[param][:, thisindex]

    return M0

#example
#plotdata = financialanalysis(D, postyear = 2015.0, S = D.A[1].S, yscale = 'abs', makeplot = 1)
