from optima import OptimaException, gitinfo, tic, toc, odict, getdate, today, uuid, dcp, objrepr, printv, findinds, saveobj, loadproj, promotetolist # Import utilities
from optima import version, loadbalancer, defaultobjectives, Project, pchip, outcomecalc
from numpy import arange, argsort, zeros, nonzero, linspace, log, exp, inf, argmax, array
from multiprocessing import Process, Queue
from glob import glob
from xlsxwriter import Workbook
import os

#######################################################################################################
## Portfolio class
#######################################################################################################

class Portfolio(object):
    """
    PORTFOLIO

    The super Optima portfolio class  -- this contains Projects and GA optimizations.

    Version: 2016jan20 by davidkedz
    """
    
    #######################################################################################################
    ## Built-in methods -- initialization, and the thing to print if you call a portfolio
    #######################################################################################################

    def __init__(self, name='default', projects=None, gaoptims=None):
        ''' Initialize the portfolio '''

        ## Set name
        self.name = name

        ## Define the structure sets
        self.projects = odict()
        if projects is not None: self.addprojects(projects)
        self.spendperproject = odict() # Store the list of the final spend per project
        self.results = None # List of before-and-after result pairs after reoptimization

        ## Define metadata
        self.uid = uuid()
        self.created = today()
        self.modified = today()
        self.version = version
        self.gitbranch, self.gitversion = gitinfo()

        return None


    def __repr__(self):
        ''' Print out useful information when called '''
        output = '============================================================\n'
        output += '            Portfolio name: %s\n' % self.name
        output += '\n'
        output += '        Number of projects: %i\n' % len(self.projects)
        output += 'Number of GA Optimizations: %i\n' % len(self.gaoptims)
        output += '\n'
        output += '            Optima version: %s\n' % self.version
        output += '              Date created: %s\n' % getdate(self.created)
        output += '             Date modified: %s\n' % getdate(self.modified)
        output += '                Git branch: %s\n' % self.gitbranch
        output += '               Git version: %s\n' % self.gitversion
        output += '                       UID: %s\n' % self.uid
        output += '============================================================\n'
        output += objrepr(self)
        return output


    #######################################################################################################
    ## Methods to handle common tasks
    #######################################################################################################

    def addprojects(self, projects=None, replace=False, verbose=2):
        ''' Store a project within portfolio '''
        printv('Adding project to portfolio...', 2, verbose)
        projects = promotetolist(projects, objtype=Project) # Make sure it's a list, but confirm type first
        if replace: self.projects = odict() # Wipe clean before adding new projects
        for project in projects:
            project.uid = uuid() # TEMPPPP WARNING overwrite UUID
            keyname = project.name if project.name not in self.projects.keys() else str(project.uid) # Only fall back on UID if the project name is taken
            self.projects[keyname] = project        
            printv('\nAdded project "%s" to portfolio "%s".' % (project.name, self.name), 2, verbose)
        return None
    
    
    def addfolder(self, folder=None, replace=True, verbose=2):
        ''' Add a folder of projects to a portfolio '''
        filelist = sorted(glob(os.path.join(folder, '*.prj')))
        projects = []
        if replace: self.projects = odict() # Wipe clean before adding new projects
        for f,filename in enumerate(filelist):
            printv('Loading project %i/%i "%s"...' % (f+1, len(filelist), filename), 3, verbose)
            project = loadproj(filename, verbose=0)
            projects.append(project)
        self.addprojects(projects, verbose=verbose)
        return None
        
        
    
    def save(self, filename=None, saveresults=False, verbose=2):
        ''' Save the current portfolio, by default using its name, and without results '''
        if filename is None and self.filename and os.path.exists(self.filename): filename = self.filename
        if filename is None: filename = self.name+'.prt'
        self.filename = os.path.abspath(filename) # Store file path
        if saveresults:
            saveobj(filename, self, verbose=verbose)
        else:
            tmpportfolio = dcp(self) # Need to do this so we don't clobber the existing results
            for P in range(len(self.projects.values())):
                tmpportfolio.projects[P].cleanresults() # Get rid of all results
            saveobj(filename, tmpportfolio, verbose=verbose) # Save it to file
            del tmpportfolio # Don't need it hanging around any more
        return None
    
    
    
    #######################################################################################################
    ## Methods to perform major tasks
    #######################################################################################################
        
    def runGA(self, grandtotal=None, objectives=None, boclist=None, npts=None, maxiters=None, maxtime=None, reoptimize=True, mc=None, batch=True, doprint=True, export=False, verbose=2):
        ''' Complete geospatial analysis process applied to portfolio for a set of objectives '''
        
        GAstart = tic()
        
        # Check inputs
        if npts is None: npts = 2000 # The number of points to calculate along each BOC
        if mc is None: mc = 0 # Do not use MC by default
        
        # Gather the BOCs
        if boclist is None:
            boclist = []
            for pno,project in enumerate(self.projects.values()):
                thisboc = project.getBOC(objectives=objectives)
                if thisboc is None:
                    errormsg = 'GA FAILED: Project %s has no BOC' % project.name
                    raise OptimaException(errormsg)
                boclist.append(thisboc)
        
        # Get the grand total
        if grandtotal is None:
            if objectives is not None:
                grandtotal = objectives['budget']
            else:
                grandtotal = 0.0
                for boc in boclist:
                    grandtotal += sum(boc.defaultbudget[:])
        
        # Run actual geospatial analysis optimization
        printv('Performing geospatial optimization for grand total budget of %0.0f' % grandtotal, 2, verbose)

        # Set up vectors
        nbocs = len(boclist)
        bocxvecs = []
        bocyvecs = []
        for boc in boclist:
            maxbudget = min(grandtotal,max(boc.x))+1 # Add one for the log
            tmpx1 = linspace(0,log(maxbudget), npts) # Exponentially distributed
            tmpx2 = linspace(1, maxbudget, npts) # Uniformly distributed
            tmpx3 = (tmpx1+log(tmpx2))/2. # Halfway in between, logarithmically speaking
            tmpxvec = exp(tmpx3)-1 # Subtract one from the log
            tmpyvec = pchip(boc.x, boc.y, tmpxvec)
            newtmpyvec = tmpyvec[0] - tmpyvec # Flip to an improvement
            bocxvecs.append(tmpxvec)
            bocyvecs.append(newtmpyvec)
        
        # Extract BOC derivatives
        relspendvecs = []
        relimprovevecs = []
        costeffvecs = []
        for b in range(nbocs):
            withinbudget = nonzero(bocxvecs[b]<=grandtotal)[0] # Stupid nonzero returns stupid
            relspendvecs.append(dcp(bocxvecs[b][withinbudget[1:]])) # Exclude 0 spend
            relimprovevecs.append(bocyvecs[b][withinbudget[1:]])
            costeffvecs.append(relimprovevecs[b]/relspendvecs[b])
        
        # Iterate over vectors, finding best option
        maxgaiters = int(1e6) # This should be a lot -- just not infinite, but should break first
        spendperproject = zeros(nbocs)
        runningtotal = grandtotal
        for i in range(maxgaiters):
            bestval = -inf
            bestboc = None
            for b in range(nbocs):
                assert(len(costeffvecs[b])==len(relimprovevecs[b])==len(relspendvecs[b]))
                if len(costeffvecs[b]):
                    tmpbestind = argmax(costeffvecs[b])
                    tmpbestval = costeffvecs[b][tmpbestind]
                    if tmpbestval>bestval:
                        bestval = tmpbestval
                        bestind = tmpbestind
                        bestboc = b
            
            # Update everything
            if bestboc is not None:
                money = relspendvecs[bestboc][bestind]
                runningtotal -= money
                relspendvecs[bestboc] -= money
                spendperproject[bestboc] += money
                relimprovevecs[bestboc] -= relimprovevecs[bestboc][bestind]
                relspendvecs[bestboc]   = relspendvecs[bestboc][bestind+1:]
                relimprovevecs[bestboc] = relimprovevecs[bestboc][bestind+1:]
                for b in range(nbocs):
                    withinbudget = nonzero(relspendvecs[b]<=runningtotal)[0]
                    relspendvecs[b] = relspendvecs[b][withinbudget]
                    relimprovevecs[b] = relimprovevecs[b][withinbudget]
                    costeffvecs[b] = relimprovevecs[b]/relspendvecs[b]
                if not i%100:
                    printv('  Allocated %0.1f%% of the portfolio budget...' % ((grandtotal-runningtotal)/float(grandtotal)*100), 2, verbose)
            else:
                break # We're done, there's nothing more to allocate
        
        # Scale to make sure budget is correct
        spendperproject = (array(spendperproject)/array(spendperproject.sum())*grandtotal).tolist()
        
        # Calculate outcomes
        origspend = zeros(nbocs)
        origoutcomes = zeros(nbocs)
        optimoutcomes = zeros(nbocs)
        for b,boc in enumerate(boclist):
            origspend[b] = sum(boclist[b].defaultbudget[:])
            origoutcomes[b] = pchip(boc.x, boc.y, origspend[b])
            optimoutcomes[b] = pchip(boc.x, boc.y, spendperproject[b])
        
        origsum = sum(origoutcomes[:])
        optsum = sum(optimoutcomes[:])
        improvement = (1.0-optsum/origsum)*100
        printv('Geospatial analysis reduced outcome from %0.0f to %0.0f (%0.1f%%)' % (origsum, optsum, improvement), 2, verbose)
        
        # Store results
        self.spendperproject = odict([(key,spp) for key,spp in zip(self.projects.keys(), spendperproject)]) # Convert to odict
        for b,boc in enumerate(boclist):
            boc.gaoptimbudget = spendperproject[b]
        
        # Reoptimize projects
        if reoptimize: reoptimizeprojects(projects=self.projects, objectives=objectives, maxtime=maxtime, maxiters=maxiters, mc=mc, batch=batch, verbose=verbose)
        
        # Tidy up
        if doprint: self.makeoutput()
        if export: self.export()
        toc(GAstart)
        return None


    # Note: Lists of lists extrax and extray allow for extra custom points to be plotted.
    def plotBOCs(self, objectives=None, initbudgets=None, optbudgets=None, deriv=False, verbose=2, extrax=None, extray=None, baseline=0):
        ''' Loop through stored projects and plot budget-outcome curves '''
        printv('Plotting BOCs...', 2, verbose)
        
        if initbudgets == None: initbudgets = [None]*len(self.projects)
        if optbudgets == None: optbudgets = [None]*len(self.projects)
        if objectives == None: 
            printv('WARNING, you have called plotBOCs on portfolio %s without specifying objectives. Using default objectives... ' % (self.name), 2, verbose)
            objectives = defaultobjectives()
            
        if not len(self.projects) == len(initbudgets) or not len(self.projects) == len(optbudgets):
            errormsg = 'Error: Plotting BOCs for %i projects with %i initial budgets (%i required) and %i optimal budgets (%i required).' % (len(self.projects), len(initbudgets), len(self.projects), len(optbudgets), len(self.projects))
            raise OptimaException(errormsg)
        
        # Loop for BOCs and then BOC derivatives.
        for c,P in enumerate(self.projects.values()):
            ax = P.plotBOC(objectives=objectives, deriv=deriv, initbudget=initbudgets[c], optbudget=optbudgets[c], returnplot=True, baseline=baseline)
            if extrax != None:            
                for k in xrange(len(extrax[c])):
                    ax.plot(extrax[c][k], extray[c][k], 'bo')
                    if baseline==0: ax.set_ylim((0,ax.get_ylim()[1])) # Reset baseline
        return None
    
    
    # WARNING: We are comparing the un-optimised outcomes of the pre-GA allocation with the re-optimised outcomes of the post-GA allocation!
    # Be very wary of the indices being used...
    def makeoutput(self, doprint=True, verbose=2):
        ''' Just displays results related to the GA run '''
        printv('Printing results...', 2, verbose)
        
        overallbudgetinit = 0
        overallbudgetopt = 0
        overalloutcomeinit = 0
        overalloutcomeopt = 0
        
        overalloutcomesplit = odict()
        for key in self.objectives['keys']:
            overalloutcomesplit['num'+key] = odict()
            overalloutcomesplit['num'+key]['init'] = 0
            overalloutcomesplit['num'+key]['opt'] = 0
        
        projnames = []
        projbudgets = []
        projcov = []
        projoutcomes = []
        projoutcomesplit = []
        
        for prj,x in enumerate(self.resultpairs.keys()):          # WARNING: Nervous about all this slicing. Problems foreseeable if format changes.
            # Figure out which indices to use
            tvector = self.resultpairs[x]['init'].tvec          # WARNING: NOT USING DT NORMALISATIONS LATER, SO ASSUME DT = 1 YEAR.
            initial = findinds(tvector, self.objectives['start'])
            final = findinds(tvector, self.objectives['end'])
            indices = arange(initial, final)
            
            projectname = self.resultpairs[x]['init'].projectinfo['name']
            initalloc = self.resultpairs[x]['init'].budget['Current']
            gaoptalloc = self.resultpairs[x]['opt'].budget['Optimal']
            initoutcome = self.resultpairs[x]['init'].improvement[0][0]     # The first 0 corresponds to best.
                                                                            # The second 0 corresponds to outcome pre-optimisation (which shouldn't matter anyway due to pre-GA budget 'init' being optimised for 0 seconds).
            gaoptoutcome = self.resultpairs[x]['opt'].improvement[0][-1]    # The -1 corresponds to outcome post-optimisation (with 'opt' being a maxtime optimisation of a post-GA budget).
            suminitalloc = sum(initalloc.values())
            sumgaoptalloc = sum(gaoptalloc.values())
            
            overallbudgetinit += suminitalloc
            overallbudgetopt += sumgaoptalloc
            overalloutcomeinit += initoutcome
            overalloutcomeopt += gaoptoutcome
            
            projnames.append(projectname)
            projbudgets.append(odict())
            projoutcomes.append(odict())
            projbudgets[prj]['init']  = initalloc
            projbudgets[prj]['opt']   = gaoptalloc
            projoutcomes[prj]['init'] = initoutcome
            projoutcomes[prj]['opt']  = gaoptoutcome
            
            projoutcomesplit.append(odict())
            projoutcomesplit[prj]['init'] = odict()
            projoutcomesplit[prj]['opt'] = odict()
            
            initpars = self.resultpairs[x]['init'].parset[0]
            optpars = self.resultpairs[x]['opt'].parset[-1]
            initprog = self.resultpairs[x]['init'].progset[0]
            optprog = self.resultpairs[x]['opt'].progset[-1]
            initcov = initprog.getprogcoverage(initalloc,self.objectives['start'],parset=initpars)
            optcov = optprog.getprogcoverage(gaoptalloc,self.objectives['start'],parset=optpars)
            
            projcov.append(odict())
            projcov[prj]['init']  = initcov
            projcov[prj]['opt']   = optcov
            
            for key in self.objectives['keys']:
                projoutcomesplit[prj]['init']['num'+key] = self.resultpairs[x]['init'].main['num'+key].tot['Current'][indices].sum()     # Again, current and optimal should be same for 0 second optimisation, but being explicit.
                projoutcomesplit[prj]['opt']['num'+key] = self.resultpairs[x]['opt'].main['num'+key].tot['Optimal'][indices].sum()
                overalloutcomesplit['num'+key]['init'] += projoutcomesplit[prj]['init']['num'+key]
                overalloutcomesplit['num'+key]['opt'] += projoutcomesplit[prj]['opt']['num'+key]
                
        ## Actually create the output
        output = ''
        output += 'Geospatial analysis results: minimize outcomes from %i to %i' % (self.objectives['start'], self.objectives['end'])
        output += '\n\n'
        output += '\n\t\tInitial\tOptimal'
        output += '\nOverall summary'
        output += '\n\tPortfolio budget:\t%0.0f\t%0.0f' % (overallbudgetinit, overallbudgetopt)
        output += '\n\tOutcome:\t%0.0f\t%0.0f' % (overalloutcomeinit, overalloutcomeopt)
        for key in self.objectives['keys']:
            output += '\n\t' + self.objectives['keylabels'][key] + ':\t%0.0f\t%0.0f' % (overalloutcomesplit['num'+key]['init'], overalloutcomesplit['num'+key]['opt'])
        
        ## Sort, then export
        projindices = argsort(projnames)
        for prj in projindices:
            output += '\n'
            output += '\n'
            output += '\n\t\tInitial\tOptimal'
            output += '\nProject: "%s"' % projnames[prj]
            output += '\n'
            output += '\n\tBudget:\t%0.0f\t%0.0f' % (sum(projbudgets[prj]['init'][:]), sum(projbudgets[prj]['opt'][:]))
            output += '\n\tOutcome:\t%0.0f\t%0.0f' % (projoutcomes[prj]['init'], projoutcomes[prj]['opt'])
            for key in self.objectives['keys']:
                output += '\n\t' + self.objectives['keylabels'][key] + ':\t%0.0f\t%0.0f' % (projoutcomesplit[prj]['init']['num'+key], projoutcomesplit[prj]['opt']['num'+key])
            output += '\n'
            output += '\n\tAllocation:'
            for prg in projbudgets[prj]['init'].keys():
                output += '\n\t%s\t%0.0f\t%0.0f' % (prg, projbudgets[prj]['init'][prg], projbudgets[prj]['opt'][prg])
            output += '\n'
            output += '\n\tCoverage (%i):' % (self.objectives['start'])
            for prg in projbudgets[prj]['init'].keys():
                initval = projcov[prj]['init'][prg]
                optval = projcov[prj]['opt'][prg]
                if initval is None: initval = 0
                if optval is None: optval = 0
                output += '\n\t%s\t%0.0f\t%0.0f' % (prg, initval, optval)
        
        # Tidy up
        if doprint: 
            print(output)
            return None
        else:
            return output
    
    
    def export(self, filename=None):
        ''' Export the results to Excel format '''
        
        if filename is None:
            filename = self.name+'-results.xlsx'
        workbook = Workbook(filename)
        worksheet = workbook.add_worksheet()
        
        # Define formatting
        originalblue = '#18C1FF' # analysis:ignore
        hotpink = '#FFC0CB' # analysis:ignore
        formats = dict()
        formats['plain'] = workbook.add_format({})
        formats['bold'] = workbook.add_format({'bold': True})
        formats['number'] = workbook.add_format({'bg_color': hotpink, 'num_format':0x04})
        colwidth = 30
        
        # Convert from a string to a 2D array
        outlist = []
        outstr = self.makeoutput(doprint=False)
        for line in outstr.split('\n'):
            outlist.append([])
            for cell in line.split('\t'):
                outlist[-1].append(cell)
        
        # Iterate over the data and write it out row by row.
        row, col = 0, 0
        for row in range(len(outlist)):
            for col in range(len(outlist[row])):
                thistxt = outlist[row][col]
                thisformat = 'plain'
                if col==0: thisformat = 'bold'
                tmptxt = thistxt.lower()
                for word in ['budget','outcome','allocation','initial','optimal','coverage']:
                    if tmptxt.find(word)>=0: thisformat = 'bold'
                if col in [2,3] and thisformat=='plain': thisformat = 'number'
                if thisformat=='number':thistxt = float(thistxt)
                worksheet.write(row, col, thistxt, formats[thisformat])
        
        worksheet.set_column(0, 3, colwidth) # Make wider
        workbook.close()
        

def reoptimizeprojects(projects=None, objectives=None, maxtime=None, maxiters=None, mc=None, batch=True, verbose=2):
    ''' Runs final optimisations for initbudgets and optbudgets so as to summarise GA optimisation '''
    
    resultpairs = odict()
    if batch:
        outputqueue = Queue()
        processes = []
    else:
        outputqueue = None
    for pind,project in enumerate(projects.values()):
        args = (project, objectives, pind, outputqueue, maxtime, maxiters, mc, batch, verbose)
        if batch:
            prc = Process(target=reoptimizeprojects_task, args=args)
            prc.start()
            prc.join()
            processes.append(prc)
        else:
            resultpair = reoptimizeprojects_task(*args)
            resultpairs[resultpair['key']] = resultpair
    if batch:
        for key in projects.values:
            resultpair = outputqueue.get()
            resultpairs[resultpair['key']] = resultpair
    
    return resultpairs      
        

def reoptimizeprojects_task(project, objectives, pind, outputqueue, maxtime, maxiters, mc, batch, verbose):
    """Batch function for final re-optimization step of geospatial analysis."""
    if batch: loadbalancer(index=pind)
    
    # Figure out which budget to use as a starting point
    boc = project.getBOC(objectives)
    totalbudget = boc.gaoptimbudget
    smallestmismatch = inf
    for budget in boc.budgets: # Could be done with argmin() but this is more explicit...
        thismismatch = abs(totalbudget-budget[:].sum())
        if thismismatch<smallestmismatch:
            closestbudget = dcp(budget)
            smallestmismatch = thismismatch
    
    # Extract info from the BOC
    args = {'which':'outcomes', 
            'project':project, 
            'parset':boc.parsetname, 
            'progset':boc.progsetname, 
            'objectives':boc.objectives, 
            'constraints':boc.constraints, 
            'totalbudget':totalbudget, 
            'origbudget':closestbudget, 
            'mc':mc,
            'verbose':verbose}

    resultpair = odict()
    
    # Run the analyses
    resultpair['init'] = outcomecalc(boc.defaultbudget, outputresults=True, doconstrainbudget=False, **args)
    resultpair['init'].name = project.name+' GA initial'
    resultpair['opt'] = project.optimize(label=project.name, **args)
    resultpair['opt'].name = project.name+' GA optimal'
    resultpair['key'] = project.name # Store the project name to avoid mix-ups

    if batch: outputqueue.put(resultpair)
    return None

   


