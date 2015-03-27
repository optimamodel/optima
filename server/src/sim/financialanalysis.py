"""
Created on Sat Nov 29 17:40:34 2014

@author: robynstuart

Version: 2015feb03
"""
from numpy import append, npv, cumsum
from setoptions import setoptions
from printv import printv
from datetime import date
from utils import smoothinterp


def financialanalysis(D, postyear=2015, S=None, rerunmodel=False, artgrowthrate=.05, discountrate=.03, treattime=[8,1,16,3,10], cd4time=[8,8,10,8,2,2], verbose=2):
    '''
    Plot financial commitment graphs
    '''
    from utils import sanitize

    printv('Running financial analysis...', 2, verbose)
    
    # Checking inputs... 
    if not(isinstance(S,dict)): 
        print('Using default S since no usable S supplied')
        S = D['S'] # If not supplied as input, copy from D
    postyear = float(postyear) # Make sure the year for turning off transmission is a float
    
    dt = D['S']['tvec'][1]-D['S']['tvec'][0]
    stepsperyear = int(round(1/dt))

    # Initialise output structure of plot data
    plotdata = {}

    # Different y axis scaling options
    costdisplays = ['total','gdp','revenue','govtexpend','totalhealth','domestichealth']

    # Initialise other internal storage structures
    people, hivcosts, artcosts = {}, {}, {}

    # Inflation adjusting
    cpi = smoothinterp(newx=D['S']['tvec'], origx=D['G']['datayears'], origy=D['data']['econ']['cpi']['past'][0], growth=D['data']['econ']['cpi']['future'][0][0])
    cpibaseyearindex = D['data']['epiyears'].index(min(D['data']['epiyears'][-1],date.today().year))

    # Set up variables for time indexing
    simtvec = S['tvec']
    noptpts = len(simtvec)

    # Get most recent ART unit costs 
    progname = 'ART'
    prognumber = D['data']['meta']['progs']['short'].index(progname)
    artunitcost = [D['data']['costcov']['cost'][prognumber][j]/D['data']['costcov']['cov'][prognumber][j] for j in range(len(D['data']['costcov']['cost'][prognumber]))]
    artunitcost = smoothinterp(newx=D['S']['tvec'], origx=D['G']['datayears'], origy=artunitcost, growth=artgrowthrate)

    # Make an even longer series for calculating the NPV
    longart = artunitcost
    for i in range(noptpts):
        longart = append(longart,[longart[-1]*(1+artgrowthrate)**D['opt']['dt']])

    # Run a simulation with the force of infection set to zero from postyear... 
    if rerunmodel:
        from model import model
        opt = setoptions(nsims=1, turnofftrans=postyear)
        S0 = model(D['G'], D['M'], D['F'][0], opt, initstate=None)
        people['existing'] = S0['people'][:,:,:]
        hivcosts['existing'] = [0.0]*noptpts

    # Extract the number of PLHIV 
    people['total'] = S['people'][:,:,:]
    hivcosts['total'] = [0.0]*noptpts
    longcosts = {} 
    
    # Interpolate costs
    for healthno, healthstate in enumerate(D['G']['healthstates']):

        # Expand
        socialcosts = smoothinterp(newx=D['S']['tvec'], origx=D['G']['datayears'], origy=D['data']['econ']['social']['past'][healthno], growth=D['data']['econ']['social']['future'][0][0])
        othercosts = smoothinterp(newx=D['S']['tvec'], origx=D['G']['datayears'], origy=D['data']['econ']['health']['past'][healthno], growth=D['data']['econ']['health']['future'][0][0])
                    
        costs = [(socialcosts[j] + othercosts[j]) for j in range(noptpts)]

        # Make an even longer series for calculating the NPV
        longothercosts, longsocialcosts = othercosts, socialcosts
        for i in range(noptpts):
            longothercosts = append(longothercosts,[longothercosts[-1]*(1+D['data']['econ']['health']['future'][0][0])**D['opt']['dt']])
            longsocialcosts = append(longsocialcosts,[longsocialcosts[-1]*(1+D['data']['econ']['social']['future'][0][0])**D['opt']['dt']])
        longcosts[healthstate] = [longothercosts[j] + longsocialcosts[j] for j in range(noptpts*2)]

        # Calculate annual non-treatment costs for all PLHIV under the baseline sim and the zero transmission sim
        coststotalthishealthstate = [people['total'][D['G'][healthstate],:,j].sum(axis = (0,1))*costs[j] for j in range(noptpts)]
        if rerunmodel:
            costsexistingthishealthstate  = [people['existing'][D['G'][healthstate],:,j].sum(axis = (0,1))*costs[j] for j in range(noptpts)]
        
        hivcosts['total'] = [hivcosts['total'][j] + coststotalthishealthstate[j] for j in range(noptpts)]
#        print('TMP'); plot(hivcosts['total']); show()
        if rerunmodel:
            hivcosts['existing'] = [hivcosts['existing'][j] + costsexistingthishealthstate[j] for j in range(noptpts)]


    # Calculate annual treatment costs for PLHIV
    tx1total = people['total'][D['G']['tx1'][0]:D['G']['fail'][-1],:,:].sum(axis=(0,1))
    tx2total = people['total'][D['G']['tx2'][0]:D['G']['tx2'][-1],:,:].sum(axis=(0,1))
    onarttotal = [tx1total[j] + tx2total[j] for j in range(noptpts)]
    artcosts['total'] = [onarttotal[j]*artunitcost[j] for j in range(noptpts)]
    
    # Calculate annual treatment costs for existing PLHIV
    if rerunmodel:
        tx1existing = people['existing'][D['G']['tx1'][0]:D['G']['fail'][-1],:,:].sum(axis=(0,1))
        tx2existing = people['existing'][D['G']['tx2'][0]:D['G']['tx2'][-1],:,:].sum(axis=(0,1))
        onartexisting = [tx1existing[j] + tx2existing[j] for j in range(noptpts)]
        artcosts['existing'] = [onartexisting[j]*artunitcost[j] for j in range(noptpts)]

    # Store cost plot data
    for plottype in ['annual','cumulative']:
        plotdata[plottype] = {}
    
    plotsubtypes = ['existing','total','future'] if rerunmodel else ['total']

    plottype='annual'
    for plotsubtype in plotsubtypes:
        plotdata[plottype][plotsubtype] = {}
        for yscalefactor in costdisplays:
            plotdata[plottype][plotsubtype][yscalefactor] = {}
            plotdata[plottype][plotsubtype][yscalefactor]['xlinedata'] = simtvec
            plotdata[plottype][plotsubtype][yscalefactor]['xlabel'] = 'Year'
            plotdata[plottype][plotsubtype][yscalefactor]['title'] = 'Annual HIV-related costs - ' + plotsubtype + ' infections'
            if yscalefactor=='total':
#                print('TMP4'); plot(hivcosts['total']); show()
                if not plotsubtype=='future': plotdata[plottype][plotsubtype][yscalefactor]['ylinedata'] = [(hivcosts[plotsubtype][j] + artcosts[plotsubtype][j])*(cpi[cpibaseyearindex]/cpi[j]) for j in range(noptpts)]
                plotdata[plottype][plotsubtype][yscalefactor]['ylabel'] = 'USD'
#                raise Exception('TMP')
            else:
                if isinstance(sanitize(D['data']['econ'][yscalefactor]['past'][0]),int): continue #raise Exception('No data have been provided for this varaible, so we cannot display the costs as a proportion of this')
                yscale = smoothinterp(newx=D['S']['tvec'], origx=D['G']['datayears'], origy=D['data']['econ'][yscalefactor]['past'][0], growth=D['data']['econ'][yscalefactor]['future'][0][0])
                if not plotsubtype=='future': plotdata[plottype][plotsubtype][yscalefactor]['ylinedata'] = [(hivcosts[plotsubtype][j] + artcosts[plotsubtype][j])/yscale[j] for j in range(noptpts)] 
                plotdata[plottype][plotsubtype][yscalefactor]['ylabel'] = 'Proportion of ' + yscalefactor

    plottype='cumulative'
    for plotsubtype in plotsubtypes:
        plotdata[plottype][plotsubtype] = {}
        plotdata[plottype][plotsubtype]['xlinedata'] = simtvec
        plotdata[plottype][plotsubtype]['xlabel'] = 'Year'
        plotdata[plottype][plotsubtype]['ylabel'] = 'USD'
        plotdata[plottype][plotsubtype]['title'] = 'Cumulative HIV-related costs - ' + plotsubtype + ' infections'
        if not plotsubtype=='future':
            plotdata[plottype][plotsubtype]['ylinedata'] = (cumsum(plotdata['annual'][plotsubtype]['total']['ylinedata'])/stepsperyear).tolist()

    if rerunmodel:
        for yscalefactor in costdisplays:
            if 'ylinedata' in plotdata['annual']['total'][yscalefactor].keys():
                plotdata['annual']['future'][yscalefactor]['ylinedata'] = [max(0.0,plotdata['annual']['total'][yscalefactor]['ylinedata'][j] - plotdata['annual']['existing'][yscalefactor]['ylinedata'][j]) for j in range(noptpts)]
        plotdata['cumulative']['future']['ylinedata'] = (cumsum(plotdata['annual']['future']['total']['ylinedata'])/stepsperyear)

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
        commitments = append(commitments, npv(discountrate, totalflows)*D['opt']['dt']*inci[i])
    
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
            if isinstance(sanitize(D['data']['econ'][yscalefactor]['past'][0]),int): continue
            yscale = smoothinterp(newx=D['S']['tvec'], origx=D['G']['datayears'], origy=D['data']['econ'][yscalefactor]['past'][0], growth=D['data']['econ'][yscalefactor]['future'][0][0])
            plotdata['commit'][yscalefactor]['ylinedata'] = [commitments[j]/yscale[j] for j in range(noptpts)]
            plotdata['commit'][yscalefactor]['ylabel'] = 'Proportion of ' + yscalefactor

    return plotdata