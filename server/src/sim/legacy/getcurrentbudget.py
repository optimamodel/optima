def getcurrentbudget(D, alloc=None, randseed=None):
    """
    Purpose: get the parameters corresponding to a given allocation. If no allocation is specified, this function also estimates the current budget
    Inputs: D, alloc (optional)
    Returns: D
    Version: 2014nov30
    """
    from makeccocs import ccoeqn, cco2eqn, coverage_params, makesamples
    from numpy import nan, zeros, array, isnan
    from liboptima.utils import perturb
    
    npts = len(D['opt']['partvec']) # Number of parameter points
    if isinstance(alloc,type(None)): 
        alloc = D['data']['origalloc'] # Initialise currentbudget if needed
        print('WARNING: No allocation provided to alterparams, using allocation %s for programs %s.' % (alloc, D['data']['meta']['progs']['short']))
    coverage = getcoverage(D=D, alloc=alloc, randseed=randseed) # Get current coverage 
 
   # Initialise parameter structure (same as D['P'])
    for param in D['P'].keys():
        if isinstance(D['P'][param], dict) and 'p' in D['P'][param].keys():
            D['P'][param]['c'] = nan+zeros((len(D['P'][param]['p']), npts))

    # Loop over programs
    for prognumber, progname in enumerate(D['data']['meta']['progs']['short']):
        
        # Loop over effects
        for effectnumber, effect in enumerate(D['programs'][prognumber]['effects']):

            popname, parname = effect['popname'], effect['param']
            
            if parname in coverage_params: # Is the affected parameter coverage?
                coveragetype = 'num' if any(j > 1 for j in D['data']['costcov']['cov'][prognumber]) else 'per'
                D['P'][parname]['c'][:] = coverage[coveragetype][prognumber,]
            else: # ... or not?
                try: # Try to get population number...
                    popnumber = D['data']['meta']['pops']['short'].index(popname)
                except: # ... or raise error if it isn't recognised
                    print('Cannot recognise population %s, it is not in %s' % (popname, D['data']['meta']['pops']['short']))
                convertedccoparams = effect['convertedccoparams']
                use_default_ccoparams = not convertedccoparams or (not isinstance(convertedccoparams, list) and isnan(convertedccoparams))
                if use_default_ccoparams:
                    convertedccoparams = setdefaultccoparams(progname=progname, param=effect['param'], pop=effect['popname'])
                if randseed>=0:
                    try:
                        convertedccoparams[0][1] = array(perturb(1,(convertedccoparams[2][1]-convertedccoparams[1][1])/2, randseed=randseed)) - 1 + convertedccoparams[0][1]
                        convertedccoparams[-1], convertedccoparams[-2] = makesamples(effect['coparams'], effect['convertedcoparams'][0], effect['convertedcoparams'][1], effect['convertedcoparams'][2], effect['convertedcoparams'][3], randseed=randseed)
                    except:
                        print('Random sampling for CCOCs failed for program %s, makesamples failed with parameters %s.' % (progname, convertedccoparams))

                D['P'][parname]['c'][popnumber] = cco2eqn(alloc[prognumber,], convertedccoparams[0]) if len(convertedccoparams[0])==4 else ccoeqn(alloc[prognumber,], convertedccoparams[0])

    return D
   
################################################################
def getcoverage(D, alloc=None, randseed=None):
    ''' Get the coverage levels corresponding to a particular allocation '''
    from numpy import zeros_like, array, isnan
    from makeccocs import cc2eqn, cceqn, gettargetpop
    from liboptima.utils import perturb
    
    allocwaslist = 0
    if isinstance(alloc,list): alloc, allocwaslist = array(alloc), 1
    coverage = {}
    coverage['num'], coverage['per'] = zeros_like(alloc), zeros_like(alloc)

    for prognumber, progname in enumerate(D['data']['meta']['progs']['short']):
        if D['programs'][prognumber]['effects']:            

            targetpop = gettargetpop(D=D, artindex=range(D['G']['nstates'])[1::], progname=progname)[-1]
            program_ccparams = D['programs'][prognumber]['convertedccparams']
            use_default_ccparams = not program_ccparams or (not isinstance(program_ccparams, list) and isnan(program_ccparams))
            if not use_default_ccparams:
                convertedccparams = D['programs'][prognumber]['convertedccparams'] 
            else:
                convertedccparams = setdefaultccparams(progname=progname)
            if randseed>=0: convertedccparams[0][1] = array(perturb(1,(array(convertedccparams[2][1])-array(convertedccparams[1][1]))/2., randseed=randseed)) - 1 + array(convertedccparams[0][1]) 
            coverage['per'][prognumber,] = cc2eqn(alloc[prognumber,], convertedccparams[0]) if len(convertedccparams[0])==2 else cceqn(alloc[prognumber,], convertedccparams[0])
            coverage['num'][prognumber,] = coverage['per'][prognumber,]*targetpop
        else:
            coverage['per'][prognumber,] = array([None]*len(alloc[prognumber,]))
            coverage['num'][prognumber,] = array([None]*len(alloc[prognumber,]))

    if allocwaslist:
        coverage['num'] = coverage['num'].tolist()
        coverage['per'] = coverage['per'].tolist()
            
    return coverage

################################################################
def getcurrentnonhivdalysaverted(D, coverage=None):
    ''' Get the non-HIV DALYs averted by a particular allocation '''
    from numpy import zeros_like, array

    coveragewaslist = 0
    if isinstance(coverage,list): coverage, coveragewaslist = array(coverage), 1
    currentnonhivdalysaverted = zeros_like(coverage)
    
    for prognumber, progname in enumerate(D['data']['meta']['progs']['short']):
        try: nonhivdalys = D['programs'][prognumber]['nonhivdalys']
        except:
            nonhivdalys = [0.]
            print('WARNING: No non-HIV DALYs found for program %s, assuming zero.' % (progname))
        currentnonhivdalysaverted[prognumber,] = array(nonhivdalys[0]*coverage[prognumber,])

    if coveragewaslist: currentnonhivdalysaverted = currentnonhivdalysaverted.tolist()
    return currentnonhivdalysaverted
    
################################################################
def setdefaultccparams(progname=None):
    '''Set default coverage levels. ONLY for use in BE. In FE, if ccocs haven't been defined then the user won't get to this step'''

    # Defaults are stored as [median, lower bound, upperbound]. 
    default_convertedccparams = [[0.8, 4.9e-06], [0.8, 4.7e-06], [0.8, 5.1e-06]]
    print('WARNING: Cost-coverage curve not found for program %s... Using defaults.' % (progname))
    return default_convertedccparams
    
################################################################
def setdefaultccoparams(progname=None, param=None, pop=None):
    '''Set default coverage levels. ONLY for use in BE. In FE, if ccocs haven't been defined then the user won't get to this step'''

    # Defaults are stored as [median, lower bound, upperbound]. 
    default_convertedccoparams = [[0.8, 4.9e-06, 0.4, 0.8, 0], [0.8, 4.7e-06, 5.1e-06, 0.4, 0.8, 0], [0.8, 4.9e-06, 0.4, 0.8, 0]]
    print('WARNING: Cost-outcome curve not found for program %s, parameter %s and population %s... Using defaults.' % (progname, param, pop))
    
    return default_convertedccoparams

################################################################
def makecoverageplot(D, optno=-1, barwidth=.35, makeplot=0):
    ''' Make coverage bar graph '''
    
    from matplotlib.pyplot import bar, xlabel, ylabel, title, xticks, legend, tight_layout, show, figure, ylim
    from numpy import arange
    import textwrap
#    import colorbrewer
#    bmap = colorbrewer.get_map('Paired', 'Qualitative', 3) # WARNING, won't work with >13
    from gridcolormap import gridcolormap
    colors = gridcolormap(2)

    error_config = {'ecolor': '0.3'}    

    plotdata = {}
    plotdata['per'] = {}
    plotdata['num'] = {}

    xlabels = [p['name'] for p in D['programs'] if p['effects']]
    xlabels = [textwrap.fill(text,width=8) for text in xlabels]
    index = arange(len(xlabels))
        
    for key in ['num','per']:
        plotdata[key] = {}
        origcov = D['optimizations'][optno]['result']['plot'][0]['alloc'][0]['coverage'][key]['best']
        opticov = D['optimizations'][optno]['result']['plot'][0]['alloc'][1]['coverage'][key]['best']

        origcovrange = [D['optimizations'][optno]['result']['plot'][0]['alloc'][0]['coverage'][key]['high'][j]-D['optimizations'][optno]['result']['plot'][0]['alloc'][0]['coverage'][key]['low'][j] for j in range(D['G']['nprogs'])]
        opticovrange = [D['optimizations'][optno]['result']['plot'][0]['alloc'][1]['coverage'][key]['high'][j]-D['optimizations'][optno]['result']['plot'][0]['alloc'][1]['coverage'][key]['low'][j] for j in range(D['G']['nprogs'])]

        plotdata[key]['orig'] = [origcov[j] for j in range(len(D['programs'])) if D['programs'][j]['effects']]
        plotdata[key]['opti'] = [opticov[j] for j in range(len(D['programs'])) if D['programs'][j]['effects']]
        plotdata[key]['origrange'] = [origcovrange[j] for j in range(len(D['programs'])) if D['programs'][j]['effects']]
        plotdata[key]['optirange'] = [opticovrange[j] for j in range(len(D['programs'])) if D['programs'][j]['effects']]

        plotdata[key]['xlabel'] = 'Programs'
        plotdata[key]['ylabel'] = 'Coverage'
        plotdata[key]['title'] = 'Coverage'
        plotdata[key]['xlabels'] = xlabels

        if makeplot:
            figure
            bar(index, plotdata[key]['orig'], barwidth, 
                label='Original',
                yerr=plotdata[key]['origrange'],
                error_kw=error_config,
                color=colors[0])
            bar(index+barwidth, plotdata[key]['opti'], barwidth, 
                label='Optimal',
                yerr=plotdata[key]['optirange'],
                error_kw=error_config,
                color=colors[1])
            xlabel(plotdata[key]['xlabel'])
            ylabel(plotdata[key]['ylabel'])
            title(plotdata[key]['title'])
            xticks(index+barwidth, plotdata[key]['xlabels'])
            if key == 'per': ylim([0,1])
            legend()
            tight_layout()
            show()

    return plotdata