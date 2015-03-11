"""
Created on Sat Nov 29 17:40:34 2014

@author: robynstuart

Version: 2015feb03
"""
from numpy import linspace, append, npv, zeros, isnan, where
from setoptions import setoptions
from printv import printv
from datetime import date


def financialanalysis(D, postyear=2015, S=None, makeplot=False, artgrowthrate=.05, discountrate=.03, treattime=[8,1,16,3,10], cd4time=[8,8,10,8,2,2], verbose=2):
    '''
    Plot financial commitment graphs
    '''
    from utils import sanitize

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

    # Inflation adjusting
    cpi = D.data.econ.cpi.past[0] # get CPI
    cpi = expanddata(cpi, len(D.S.tvec)*D.opt.dt, D.data.econ.cpi.future[0][0], interp=True, dt=D.opt.dt)
    cpibaseyearindex = D.data.econyears.index(date.today().year)

    # Set up variables for time indexing
    simtvec = S.tvec
    noptpts = len(simtvec)

    # Get most recent ART unit costs #TODO use a series not a point!
    progname = 'ART'
    prognumber = D.data.meta.progs.short.index(progname)
    artunitcost = [D.data.costcov.cost[prognumber][j]/D.data.costcov.cov[prognumber][j] for j in range(len(D.data.costcov.cost[prognumber]))]
    artunitcost = expanddata(artunitcost, len(D.S.tvec)*D.opt.dt, artgrowthrate, interp=True, dt=D.opt.dt)

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

        # Expand
        socialcosts = expanddata(D.data.econ.social.past[healthno], len(D.S.tvec)*D.opt.dt, D.data.econ.social.future[0][0], interp=True, dt=D.opt.dt)
        othercosts = expanddata(D.data.econ.health.past[healthno], len(D.S.tvec)*D.opt.dt, D.data.econ.health.future[0][0], interp=True, dt=D.opt.dt)
                    
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
                        if not plotsubtype=='future': plotdata[plottype][plotsubtype][yscalefactor]['ylinedata'] = [(hivcosts[plotsubtype][j] + artcosts[plotsubtype][j])*(cpi[cpibaseyearindex]/cpi[j]) for j in range(noptpts)]
                        plotdata[plottype][plotsubtype][yscalefactor]['ylabel'] = 'USD'
                    else:
                        if isinstance(sanitize(D.data.econ[yscalefactor].past[0]),int): continue #raise Exception('No data have been provided for this varaible, so we cannot display the costs as a proportion of this')
                        yscale = expanddata(data=D.data.econ[yscalefactor].past[0], length=len(D.S.tvec)*D.opt.dt, growthrate=D.data.econ[yscalefactor].future[0][0], interp=True, dt=D.opt.dt)
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
        if yscalefactor=='total':                    
            plotdata['commit'][yscalefactor]['ylinedata'] = [commitments[j]*(cpi[cpibaseyearindex]/cpi[j]) for j in range(len(commitments))]
            plotdata['commit'][yscalefactor]['ylabel'] = 'USD'
        else:
            if isinstance(sanitize(D.data.econ[yscalefactor].past[0]),int): continue
            yscale = expanddata(data=D.data.econ[yscalefactor].past[0], length=len(D.S.tvec)*D.opt.dt, growthrate=D.data.econ[yscalefactor].future[0][0], dt=D.opt.dt)
            plotdata['commit'][yscalefactor]['ylinedata'] = [commitments[j]/yscale[j] for j in range(noptpts)]
            plotdata['commit'][yscalefactor]['ylabel'] = 'Proportion of ' + yscalefactor

    return plotdata
    
def expanddata(data, length, growthrate, interp=True, dt=None):
    '''
    Expand missing data set into full data 
    '''
    from utils import sanitize, smoothinterp
    
    newdata = zeros(int(length)) # make an array of zeros of the desired length
    olddata = sanitize(data) # remove nans from original data set
    for i in range(len(data)):
        if not isnan(data[i]): newdata[i] = data[i] # replace the zeros with numbers where available
    firstindex = where(newdata==olddata[0])[0][0] # find the first year for which data are available
    lastindex = where(newdata==olddata[-1])[0][0] # find the last year for which data are available
    for i in range(firstindex):
        newdata[firstindex-(i+1)] = newdata[firstindex-i]/(1+growthrate) # back-project using growth rates
    for i in range(len(newdata)-lastindex-1):
        newdata[lastindex+i+1] = newdata[lastindex+i]*(1+growthrate) # forward-project using growth rates
    if interp: # if required, interpolate between years
        newx = linspace(0,1,int(length/dt))
        origx = linspace(0,1,len(newdata))
        newdata = smoothinterp(newx, origx, newdata, smoothness=5)
    
    return newdata


# Test code -- #TODO don't commit with this here. 
#plotdata = financialanalysis(D)
#from matplotlib.pylab import figure, plot, hold
#figure()
#hold(True)
#plot(plotdata['commit']['total']['xlinedata'],plotdata['commit']['total']['ylinedata'])
#figure()
#hold(True)
#plot(plotdata['commit']['total']['xlinedata'],D.S.inci.sum(axis=0))

