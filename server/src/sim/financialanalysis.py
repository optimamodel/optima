"""
Created on Sat Nov 29 17:40:34 2014

@author: robynstuart

Version: 2015feb03
"""
from numpy import linspace, append, npv, zeros, isnan, where
from setoptions import setoptions
from utils import sanitize, smoothinterp
from printv import printv

def financialanalysis(D, postyear=2015, S=None, makeplot=False, artgrowthrate=.03, discountrate=.03, treattime=[8,1,16,3,10], cd4time=[8,8,10,8,2,2], verbose=2):
    '''
    Plot financial commitment graphs
    '''
    printv('Running financial analysis...', 2, verbose)
    
    # Checking inputs... 
    if not(isinstance(S,dict)): 
        print('Using default S since no usable S supplied')
        S = D.S # If not supplied as input, copy from D
    postyear = float(postyear) # Make sure the year for turning off transmission is a float

    # Initialise output structure of plot data
    plotdata = {}

    # Different y axis scaling options
    costdisplays = ['total','gdp','revenue','govtexpend','totalhealth','domestichealth']

    # Initialise other internal storage structures
    people, hivcosts, artcosts = {}, {}, {}

    # Set up variables for time indexing
    simtvec = S.tvec
    noptpts = len(simtvec)

    # Get most recent ART unit costs #TODO use a series not a point!
    progname = 'ART'
    prognumber = D.data.meta.progs.short.index(progname)
    newart = zeros(int(len(D.S.tvec)*D.opt.dt))
    for j in range(len(D.data.costcov.cost[prognumber])):
        if not isnan(D.data.costcov.cost[prognumber][j]/D.data.costcov.cov[prognumber][j]): newart[j] = D.data.costcov.cost[prognumber][j]/D.data.costcov.cov[prognumber][j]
    oldart = sanitize([D.data.costcov.cost[prognumber][j]/D.data.costcov.cov[prognumber][j] for j in range(len(D.data.costcov.cov[prognumber]))])
    firstartindex = where(newart==oldart[0])[0][0]
    lastartindex = where(newart==oldart[-1])[0][0]
    for i in range(firstartindex):
        newart[firstartindex-i-1] = newart[firstartindex-i]/(1+artgrowthrate)
    for i in range(len(newart)-lastartindex-1):
        newart[lastartindex+i+1] = newart[lastartindex+i]*(1+artgrowthrate)
    newx = linspace(0,1,noptpts)
    origx = linspace(0,1,len(newart))
    artunitcost = smoothinterp(newx, origx, newart, smoothness=5)

    # Make an even longer series for calculating the NPV
    longart = artunitcost
    for i in range(noptpts):
        longart = append(longart,[longart[-1]*(1+artgrowthrate)**D.opt.dt])

    # Run a simulation with the force of infection set to zero from postyear... 
    from model import model
    opt = setoptions(nsims=1, turnofftrans=postyear)
    S0 = model(D.G, D.M, D.F[0], opt, initstate=None)

    # Extract the number of PLHIV under the baseline sim and the zero transmission sim
    people['total'] = S.people[:,:,:]
    people['existing'] = S0.people[:,:,:]
    hivcosts['total'] = [0.0]*noptpts
    hivcosts['existing'] = [0.0]*noptpts
    longcosts = {} 
    
    # Interpolate costs
    for healthno, healthstate in enumerate(D.G.healthstates):

        # Remove NaNs from data
        socialcosts = sanitize(D.data.econ.social.past[healthno])
        othercosts = sanitize(D.data.econ.health.past[healthno])
        
        # Extrapolate
        newsocial, newother = zeros(int(len(D.S.tvec)*D.opt.dt)), zeros(int(len(D.S.tvec)*D.opt.dt))
        for i in range(len(D.data.econ.social.past[healthno])):
            if not isnan(D.data.econ.social.past[healthno][i]): newsocial[i] = D.data.econ.social.past[healthno][i]
            if not isnan(D.data.econ.health.past[healthno][i]): newother[i] = D.data.econ.health.past[healthno][i]
        lastsocialindex = where(newsocial==socialcosts[-1])[0][0]
        lastotherindex = where(newother==othercosts[-1])[0][0]
        firstsocialindex = where(newsocial==socialcosts[0])[0][0]
        firstotherindex = where(newother==othercosts[0])[0][0]

        for i in range(len(newsocial)-lastsocialindex-1):
            newsocial[lastsocialindex+i+1] = newsocial[lastsocialindex+i]*(1+D.data.econ.social.future[0][0])
        for i in range(len(newother)-lastotherindex-1):
            newother[lastotherindex+i+1] = newother[lastotherindex+i]*(1+D.data.econ.health.future[0][0])

        for i in range(firstsocialindex):
            newsocial[firstsocialindex-i-1] = newsocial[firstsocialindex-i]/(1+D.data.econ.social.future[0][0])
        for i in range(firstotherindex):
            newother[firstotherindex-i-1] = newother[firstotherindex-i]/(1+D.data.econ.health.future[0][0])

        # Interpolating
        origx = linspace(0,1,len(newsocial))
        socialcosts = smoothinterp(newx, origx, newsocial, smoothness=5)
        origx = linspace(0,1,len(newother))
        othercosts = smoothinterp(newx, origx, newother, smoothness=5)
            
        costs = [(socialcosts[j] + othercosts[j]) for j in range(noptpts)]

        # Make an even longer series for calculating the NPV
        longothercosts, longsocialcosts = othercosts, socialcosts
        for i in range(noptpts):
            longothercosts = append(longothercosts,[longothercosts[-1]*(1+D.data.econ.health.future[0][0])**D.opt.dt])
            longsocialcosts = append(longsocialcosts,[longsocialcosts[-1]*(1+D.data.econ.social.future[0][0])**D.opt.dt])
        longcosts[healthstate] = [longothercosts[j] + longsocialcosts[j] for j in range(noptpts*2)]

        # Calculate annual non-treatment costs for all PLHIV under the baseline sim and the zero transmission sim
        coststotalthishealthstate = [people['total'][D.G[healthstate],:,j].sum(axis = (0,1))*costs[j] for j in range(noptpts)]
        costsexistingthishealthstate  = [people['existing'][D.G[healthstate],:,j].sum(axis = (0,1))*costs[j] for j in range(noptpts)]
        
        hivcosts['total'] = [hivcosts['total'][j] + coststotalthishealthstate[j] for j in range(noptpts)]
        hivcosts['existing'] = [hivcosts['existing'][j] + costsexistingthishealthstate[j] for j in range(noptpts)]

    # Calculate annual treatment costs for PLHIV
    tx1total = people['total'][D.G.tx1[0]:D.G.fail[-1],:,:].sum(axis=(0,1))
    tx2total = people['total'][D.G.tx2[0]:D.G.tx2[-1],:,:].sum(axis=(0,1))
    onarttotal = [tx1total[j] + tx2total[j] for j in range(noptpts)]
    artcosts['total'] = [onarttotal[j]*artunitcost[j] for j in range(noptpts)]
    
    # Calculate annual treatment costs for existing PLHIV
    tx1existing = people['existing'][D.G.tx1[0]:D.G.fail[-1],:,:].sum(axis=(0,1))
    tx2existing = people['existing'][D.G.tx2[0]:D.G.tx2[-1],:,:].sum(axis=(0,1))
    onartexisting = [tx1existing[j] + tx2existing[j] for j in range(noptpts)]
    artcosts['existing'] = [onartexisting[j]*artunitcost[j] for j in range(noptpts)]

    # Cumulative sum function (b/c can't find an inbuilt one)
    def accumu(lis):
        total = 0
        for x in lis:
            total += x*D.opt.dt
            yield total

    # Store cost plot data
    for plottype in ['annual','cumulative']:
        plotdata[plottype] = {}
        for plotsubtype in ['existing','total','future']:
            plotdata[plottype][plotsubtype] = {}
            if plottype=='annual':
                for yscalefactor in costdisplays:
                    plotdata[plottype][plotsubtype][yscalefactor] = {}
                    plotdata[plottype][plotsubtype][yscalefactor]['xlinedata'] = simtvec
                    plotdata[plottype][plotsubtype][yscalefactor]['xlabel'] = 'Year'
                    plotdata[plottype][plotsubtype][yscalefactor]['title'] = 'Annual HIV-related costs - ' + plotsubtype + ' infections'
                    if yscalefactor=='total':                    
                        if not plotsubtype=='future': plotdata[plottype][plotsubtype][yscalefactor]['ylinedata'] = [(hivcosts[plotsubtype][j] + artcosts[plotsubtype][j]) for j in range(noptpts)]
                        plotdata[plottype][plotsubtype][yscalefactor]['ylabel'] = 'USD'
                    else:
                        yscale = sanitize(D.data.econ[yscalefactor].past)
                        if isinstance(yscale,int): continue #raise Exception('No data have been provided for this varaible, so we cannot display the costs as a proportion of this')
                        for i in range(int(D.S.tvec[-1]-D.G.dataend)):
                            yscale = append(yscale,[yscale[-1]*(1+D.data.econ[yscalefactor].future[0][0])])
                        origx = linspace(0,1,len(yscale))
                        yscale = smoothinterp(newx, origx, yscale, smoothness=5)                            
                        if not plotsubtype=='future': plotdata[plottype][plotsubtype][yscalefactor]['ylinedata'] = [(hivcosts[plotsubtype][j] + artcosts[plotsubtype][j])/yscale[j] for j in range(noptpts)] 
                        plotdata[plottype][plotsubtype][yscalefactor]['ylabel'] = 'Proportion of ' + yscalefactor
            else:
                plotdata[plottype][plotsubtype]['xlinedata'] = simtvec
                plotdata[plottype][plotsubtype]['xlabel'] = 'Year'
                plotdata[plottype][plotsubtype]['ylabel'] = 'USD'
                plotdata[plottype][plotsubtype]['title'] = 'Cumulative HIV-related costs - ' + plotsubtype + ' infections'
                if not plotsubtype=='future': plotdata[plottype][plotsubtype]['ylinedata'] = list(accumu([hivcosts[plotsubtype][j] + artcosts[plotsubtype][j] for j in range(noptpts)]))

    for yscalefactor in costdisplays:
        if 'ylinedata' in plotdata['annual']['total'][yscalefactor].keys():
            plotdata['annual']['future'][yscalefactor]['ylinedata'] = [max(0.0,plotdata['annual']['total'][yscalefactor]['ylinedata'][j] - plotdata['annual']['existing'][yscalefactor]['ylinedata'][j]) for j in range(noptpts)]
    plotdata['cumulative']['future']['ylinedata'] = list(accumu(plotdata['annual']['future']['total']['ylinedata']))

    # Calculate net present value of future stream of treatment costs
    inci = S.inci.sum(axis=0)
    commitments = []
    for i in range(len(inci)):
        artflows = longart[i+treattime[0]+treattime[1]:i+treattime[0]+treattime[1]+treattime[2]].tolist() + \
                   longart[i+treattime[0]+treattime[1]+treattime[2]:i+treattime[0]+treattime[1]+treattime[2]+treattime[3]].tolist() + \
                   longart[i+treattime[0]+treattime[1]+treattime[2]+treattime[3]:i+treattime[0]+treattime[1]+treattime[2]+treattime[3]+treattime[4]].tolist()
        otherflows = longcosts['acute'][i:i+cd4time[0]] + \
                     longcosts['gt500'][i+cd4time[0]:i+cd4time[0]+cd4time[1]] + \
                     longcosts['gt350'][i+cd4time[0]+cd4time[1]:i+cd4time[0]+cd4time[1]+cd4time[2]] + \
                     longcosts['gt200'][i+cd4time[0]+cd4time[1]+cd4time[2]:i+cd4time[0]+cd4time[1]+cd4time[2]+cd4time[3]] + \
                     longcosts['gt50'][i+cd4time[0]+cd4time[1]+cd4time[2]+cd4time[3]:i+cd4time[0]+cd4time[1]+cd4time[2]+cd4time[3]+cd4time[4]] + \
                     longcosts['aids'][i+cd4time[0]+cd4time[1]+cd4time[2]+cd4time[3]+cd4time[4]:i+cd4time[0]+cd4time[1]+cd4time[2]+cd4time[3]+cd4time[4]+cd4time[5]]
        totalflows = [artflows[j]+otherflows[j] for j in range(len(artflows))]
        commitments = append(commitments, npv(discountrate, totalflows)*D.opt.dt*inci[i])
    
    # Store commitment cost data
    plotdata['commit'] = {}
    for yscalefactor in costdisplays:
        plotdata['commit'][yscalefactor] = {}
        plotdata['commit'][yscalefactor]['xlinedata'] = simtvec
        plotdata['commit'][yscalefactor]['xlabel'] = 'Year'
        plotdata['commit'][yscalefactor]['title'] = 'Annual spending commitments from new HIV infections'
        if isinstance(yscale,int): continue
        if yscalefactor=='total':                    
            plotdata['commit'][yscalefactor]['ylinedata'] = commitments
            plotdata['commit'][yscalefactor]['ylabel'] = 'USD'
        else:
            plotdata['commit'][yscalefactor]['ylinedata'] = [commitments[j]/yscale[j] for j in range(noptpts)]
            plotdata['commit'][yscalefactor]['ylabel'] = 'Proportion of ' + yscalefactor

    return plotdata

# Test code -- #TODO don't commit with this here. 
#plotdata = financialanalysis(D)
#from matplotlib.pylab import figure, plot, hold
#figure()
#hold(True)
#plot(plotdata['commit']['total']['xlinedata'],plotdata['commit']['total']['ylinedata'])

