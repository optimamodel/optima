from optima import OptimaException, Link, gitinfo, tic, toc, odict, getdate, today, uuid, dcp, objrepr, makefilepath, printv, findnearest, saveobj, loadproj, promotetolist # Import utilities
from optima import version, defaultobjectives, Project, pchip, getfilelist, batchBOC, reoptimizeprojects
from numpy import arange, argsort, zeros, nonzero, linspace, log, exp, inf, argmax, array
from xlsxwriter import Workbook
from xlsxwriter.utility import xl_rowcol_to_cell as rc
from xlrd import open_workbook
import re

__all__ = [
    'Portfolio',
    'makegeospreadsheet',
    'makegeoprojects'
]

#######################################################################################################
## Portfolio class
#######################################################################################################

class Portfolio(object):
    """
    PORTFOLIO

    The super Optima portfolio class  -- this contains Projects and GA optimizations.

    Version: 2016jan20 
    """
    
    #######################################################################################################
    ## Built-in methods -- initialization, and the thing to print if you call a portfolio
    #######################################################################################################

    def __init__(self, name='default', objectives=None, projects=None):
        ''' Initialize the portfolio '''

        ## Set name
        self.name = name

        ## Define the structure sets
        self.projects = odict()
        self.objectives = objectives
        if projects is not None: self.addprojects(projects)
        self.spendperproject = odict() # Store the list of the final spend per project
        self.results = odict() # List of before-and-after result pairs after reoptimization

        ## Define metadata
        self.uid = uuid()
        self.created = today()
        self.modified = today()
        self.version = version
        self.gitbranch, self.gitversion = gitinfo()
        self.filename = None # File path, only present if self.save() is used

        return None


    def __repr__(self):
        ''' Print out useful information when called '''
        output = '============================================================\n'
        output += '            Portfolio name: %s\n' % self.name
        output += '\n'
        output += '        Number of projects: %i\n' % len(self.projects)
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
            project.uid = uuid() # WARNING overwrite UUID
            keyname = project.name if project.name not in self.projects.keys() else str(project.uid) # Only fall back on UID if the project name is taken
            self.projects[keyname] = project        
            printv('Added project %s to portfolio %s' % (project.name, self.name), 2, verbose)
        return None
    
    
    def addfolder(self, folder=None, replace=True, pattern=None, verbose=2):
        ''' Add a folder of projects to a portfolio '''
        filelist = getfilelist(folder, 'prj', pattern=pattern)
        projects = []
        if replace: self.projects = odict() # Wipe clean before adding new projects
        for f,filename in enumerate(filelist):
            printv('Loading project %i/%i "%s"...' % (f+1, len(filelist), filename), 3, verbose)
            project = loadproj(filename, verbose=0)
            projects.append(project)
        self.addprojects(projects, verbose=verbose)
        return None
        
        
    
    def save(self, filename=None, folder=None, saveresults=True, verbose=2, cleanparsfromscens=None):
        ''' Save the current portfolio, by default using its name, and without results '''
        if cleanparsfromscens is None: cleanparsfromscens = not saveresults  # Default to cleaning if we are not saving results
        fullpath = makefilepath(filename=filename, folder=folder, default=[self.filename, self.name], ext='prt', sanitize=True)
        self.filename = fullpath # Store file path
        printv('Saving portfolio to %s...' % self.filename, 2, verbose)
        
        # Easy -- just save the whole thing
        if saveresults and not cleanparsfromscens:
            saveobj(fullpath, self, verbose=verbose)
        
        # Hard -- have to make a copy, remove results, and restore links
        else:
            tmpportfolio = dcp(self) # Need to do this so we don't clobber the existing results
            for P in self.projects.values():
                if not saveresults:    P.cleanresults()       # Get rid of all results
                if cleanparsfromscens: P.cleanparsfromscens() # Get rid of pars and scenparsets from scenarios which are not needed
                P.restorelinks()  # Restore links in projects
            if tmpportfolio.results: # Restore project links in results, but only iterate over it if it's populated
                for key,resultpair in tmpportfolio.results.items():
                    for result in resultpair.values():
                        if hasattr(result, 'projectref'): # Check, because it may not be a result
                            result.projectref = Link(tmpportfolio.projects[key]) # Recreate the link
            saveobj(fullpath, tmpportfolio, verbose=verbose) # Save it to file
            del tmpportfolio # Don't need it hanging around any more
        
        return fullpath
    
    
    
    #######################################################################################################
    ## Methods to perform major tasks
    #######################################################################################################
    
    def genBOCs(self, budgetratios=None, name=None, parsetname=None, progsetname=None, objectives=None, constraints=None,
            absconstraints=None, proporigconstraints=None, maxiters=200, maxtime=None, verbose=2, stoppingfunc=None,
            maxload=0.5, interval=None, prerun=True, batch=True, mc=3, die=False, recalculate=True, strict=True, randseed=None,
            parallel=None, ncpus=None, finishtime=None):
        '''
        Just like genBOC, but run on each of the projects in the portfolio. See batchBOC() for explanation
        of kwargs.
        
        Version: 2017may22
        '''
        
        # If objectives not supplied, use the ones from the portfolio
        if objectives is None: objectives = self.objectives
        
        # All we need to do is run batchBOC on the portfolio's odict of projects
        self.projects = batchBOC(projects=self.projects, budgetratios=budgetratios, name=name, parsetname=parsetname, progsetname=progsetname,
            objectives=objectives, constraints=constraints, absconstraints=absconstraints, proporigconstraints=proporigconstraints,
            maxiters=maxiters, maxtime=maxtime, verbose=verbose, stoppingfunc=stoppingfunc, maxload=maxload, interval=interval,
            prerun=prerun, batch=batch, mc=mc, die=die, recalculate=recalculate, strict=strict, randseed=randseed, parallel=parallel,
            ncpus=ncpus, finishtime=finishtime)
             
        return None
        
    
    def runGA(self, grandtotal=None, objectives=None, npts=None, maxiters=None, maxtime=None, reoptimize=True, mc=None, batch=True, maxload=None, interval=None, doprint=True, export=False, outfile=None, verbose=2, die=True, strict=True, randseed=None):
        ''' Complete geospatial analysis process applied to portfolio for a set of objectives '''
        
        GAstart = tic()
        
        # Check inputs
        if npts is None: npts = 2000 # The number of points to calculate along each BOC
        if mc is None: mc = 0 # Do not use MC by default
        if objectives is not None: self.objectives = objectives # Store objectives, if supplied
        else:                      objectives = self.objectives # Else, replace with stored objectives
        
        def gatherBOCs():
            ''' Gather the BOCs -- called twice which is why it's a function '''
            bocsvalid = True
            boclist = []
            for pno,project in enumerate(self.projects.values()):
                thisboc = project.getBOC(objectives=objectives, strict=strict)
                if thisboc is None:
                    bocsvalid = False
                    errormsg = 'GA FAILED: Project %s has no BOC' % project.name
                    if die: raise OptimaException(errormsg) # By default die here, but optionally just recalculate
                    else:   printv(errormsg, 1, verbose)
                boclist.append(thisboc)
            return boclist, bocsvalid
        
        # If any BOCs failed, recalculate the ones that did     
        boclist, bocsvalid = gatherBOCs() # If die==True, this will crash if a BOC isn't found; otherwise, return False
        if not bocsvalid:
            self.genBOCs(objectives=objectives, maxiters=maxiters, maxtime=maxtime, mc=mc, batch=batch, maxload=maxload, interval=interval, verbose=verbose, die=die, randseed=randseed, recalculate=False)
            boclist, bocsvalid = gatherBOCs() # Seems odd to repeat this here...
        
        # Get the grand total
        if grandtotal is None:
            if objectives is not None and objectives['budget']: # If 0, then calculate based on the BOCs
                grandtotal = objectives['budget']
            else:
                grandtotal = 0.0
                for boc in boclist:
                    grandtotal += sum(boc.defaultbudget[:])
        if not grandtotal:
            errormsg = 'Total budget of all %i projects included in this portfolio is zero' % len(self.projects)
            raise OptimaException(errormsg)
        
        # Really store the objectives
        if self.objectives is None:
            self.objectives = boclist[0].objectives
            self.objectives['budget'] = grandtotal
        
        # Run actual geospatial analysis optimization
        printv('Performing geospatial optimization for grand total budget of %0.0f' % grandtotal, 2, verbose)

        # Set up vectors
        nbocs = len(boclist)
        bocxvecs = []
        bocyvecs = []
        for boc in boclist:
            maxbudget = min(grandtotal,max(boc.x)) # Calculate the maximum sensible budget for this region
            tmpx1 = linspace(1,log(maxbudget), npts) # Logarithmically distributed
            tmpx2 = log(linspace(1, maxbudget, npts)) # Uniformly distributed
            tmpx3 = (tmpx1+tmpx2)/2. # Halfway in between, logarithmically speaking
            tmpxvec = exp(tmpx3) # Convert from log-space to normal space
            tmpyvec = pchip(boc.x, boc.y, tmpxvec) # Interpolate BOC onto the new points
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
        oldpercentcomplete = 0.0 # Keep track of progress
        for i in range(maxgaiters):
            bestval = -inf
            bestboc = None
            for b in range(nbocs):
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
                newpercentcomplete = (grandtotal-runningtotal)/float(grandtotal)*100
                if not(i%100) or (newpercentcomplete-oldpercentcomplete)>1.0:
                    printv('  Allocated %0.1f%% of the portfolio budget...' % newpercentcomplete, 2, verbose)
                    oldpercentcomplete = newpercentcomplete
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
        if reoptimize: 
            resultpairs = reoptimizeprojects(projects=self.projects, objectives=objectives, maxtime=maxtime, maxiters=maxiters, mc=mc, batch=batch, maxload=maxload, interval=interval, verbose=verbose, randseed=randseed)
            self.results = resultpairs
            for b,boc in enumerate(boclist):
                boc.ygaoptim = self.results[b]['opt'].outcome # Store outcome
        
        # Make results and optionally export
        if self.results: self.makeoutput(doprint=doprint, verbose=verbose)
        if export:
            if self.results:
                self.export(filename=outfile, verbose=verbose)
            else:
                errormsg = 'Could not export results for portfolio %s since no results generated' % self.name
                raise OptimaException(errormsg)
        
        toc(GAstart)
        return None


    # Note: Lists of lists extrax and extray allow for extra custom points to be plotted.
    def plotBOCs(self, objectives=None, initbudgets=None, optbudgets=None, deriv=False, verbose=2, extrax=None, extray=None, baseline=0):
        ''' Loop through stored projects and plot budget-outcome curves '''
        printv('Plotting BOCs...', 2, verbose)
        
        if initbudgets == None: initbudgets = [None]*len(self.projects)
        if optbudgets == None: optbudgets = [None]*len(self.projects)
        if objectives == None: 
            try: 
                objectives = self.objectives # This should be defined, but just in case...
            except:
                printv('WARNING, you have called plotBOCs on portfolio %s without specifying objectives. Using default objectives... ' % (self.name), 2, verbose)
                objectives = defaultobjectives()
            
        if not len(self.projects) == len(initbudgets) or not len(self.projects) == len(optbudgets):
            errormsg = 'Error: Plotting BOCs for %i projects with %i initial budgets (%i required) and %i optimal budgets (%i required).' % (len(self.projects), len(initbudgets), len(self.projects), len(optbudgets), len(self.projects))
            raise OptimaException(errormsg)
        
        # Loop for BOCs and then BOC derivatives.
        for c,P in enumerate(self.projects.values()):
            ax = P.plotBOC(objectives=objectives, deriv=deriv, initbudget=initbudgets[c], optbudget=optbudgets[c], returnplot=True, baseline=baseline)
            if extrax != None:            
                for k in range(len(extrax[c])):
                    ax.plot(extrax[c][k], extray[c][k], 'bo')
                    if baseline==0: ax.set_ylim((0,ax.get_ylim()[1])) # Reset baseline
        return None
    
    
    def makeoutput(self, doprint=False, verbose=2):
        ''' Just displays results related to the GA run '''
        if doprint: printv('Printing results...', 2, verbose)
        if not self.results:
            errormsg = 'Portfolio does not contain results: most likely geospatial analysis has not been run'
            raise OptimaException(errormsg)
        self.GAresults  = odict() # I can't believe this wasn't stored before
        bestindex = 0 # Index of the best result -- usually 0 since [best, low, high]  
        
        # Keys for initial and optimized
        iokeys = ['init', 'opt'] 
        
        # Labels and denominators for determining output across a GA
        denominators = odict([('propdiag','numplhiv'), ('proptreat','numdiag'), ('propsuppressed','numtreat')]) 
        
        # Initialize to zero
        projnames        = []
        projbudgets      = []
        projcov          = []
        projoutcomes     = []
        projoutcomesplit = []
        overallbud       = odict() # Overall budget
        overallout       = odict() # Overall outcomes
        for io in iokeys:
            overallbud[io] = 0
            overallout[io] = 0
        
        # Set up dict for the outcome split
        overalloutcomesplit = odict()
        denominator = odict()
        for obkey in self.objectives['keys']:
            overalloutcomesplit['num'+obkey] = odict()
            for io in iokeys:
                overalloutcomesplit['num'+obkey][io] = 0
        for caskey in self.objectives['cascadekeys']:
            overalloutcomesplit[caskey] = odict()
            denominator[caskey] = odict()
            for io in iokeys:
                overalloutcomesplit[caskey][io] = 0
                denominator[caskey][io] = 0
        
        for k,reskey in enumerate(self.results.keys()):
            # Figure out which indices to use
            projectname = self.results[reskey]['init'].projectinfo['name']
            projnames.append(projectname)
            projbudgets.append(odict())
            projoutcomes.append(odict())
            projoutcomesplit.append(odict())
            projcov.append(odict())
            tvector, initial, final, indices, alloc, outcome, sumalloc = [odict() for o in range(7)] # Allocate all dicts
            for io in iokeys:
                tvector[io]  = self.results[reskey][io].tvec # WARNING, can differ between initial and optimized!
                initial[io]  = findnearest(tvector[io], self.objectives['start'])
                final[io]    = findnearest(tvector[io], self.objectives['end'])
                indices[io]  = arange(initial[io], final[io])
                alloc[io]    = self.results[reskey][io].budgets[-1]
                outcome[io]  = self.results[reskey][io].outcome 
                sumalloc[io] = alloc[io][:].sum() # Should be a budget odict that we're summing
                
                overallbud[io] += sumalloc[io]
                overallout[io] += outcome[io]
                projbudgets[k][io]  = alloc[io]
                projoutcomes[k][io] = outcome[io]
                
                thisioresult = self.results[reskey][io]
                tmppars = thisioresult.projectref().parsets[thisioresult.parsetname]
                tmpprog = thisioresult.projectref().progsets[thisioresult.progsetname]
                tmpcov = tmpprog.getprogcoverage(alloc[io], self.objectives['start'], parset=tmppars)
                projcov[k][io]  = tmpcov
                
                projoutcomesplit[k][io] = odict()
                for obkey in self.objectives['keys']:
                    projoutcomesplit[k][io]['num'+obkey] = self.results[reskey][io].main['num'+obkey].tot[bestindex][indices[io]].sum()     # Again, current and optimal should be same for 0 second optimisation, but being explicit -- WARNING, need to fix properly!
                    overalloutcomesplit['num'+obkey][io] += projoutcomesplit[k][io]['num'+obkey]
                for caskey in self.objectives['cascadekeys']:
                    denominator[caskey][io] =  self.results[reskey][io].main[denominators[caskey]].tot[bestindex][indices[io]].sum()  #need to weight results by population size
                    projoutcomesplit[k][io][caskey] = self.results[reskey][io].main[caskey].tot[bestindex][indices[io]].sum()     # Again, current and optimal should be same for 0 second optimisation, but being explicit -- WARNING, need to fix properly!
                    overalloutcomesplit[caskey][io] += projoutcomesplit[k][io][caskey] * denominator[caskey][io]
        
        # Divide by population size to get the correct proportional outcome across projects
        for io in iokeys:
            for caskey in self.objectives['cascadekeys']:
                if denominator[caskey][io]>0:
                    overalloutcomesplit[caskey][io] /= denominator[caskey][io]
                else:
                    overalloutcomesplit[caskey][io] = 0. #nan?
        
        # Add to the results structure
        self.GAresults['overallbudget']       = overallbud
        self.GAresults['overalloutcomes']     = overallout
        self.GAresults['overalloutcomesplit'] = overalloutcomesplit
        self.GAresults['projectbudgets']      = projbudgets
        self.GAresults['projectcoverages']    = projcov
        self.GAresults['projectoutcomes']     = projoutcomes
        self.GAresults['projectoutcomesplit'] = projoutcomesplit
        
        # Create the text output
        output = ''
        output += 'Geospatial analysis results: minimize outcomes from %i to %i' % (self.objectives['start'], self.objectives['end'])
        output += '\n\n'
        output += '\n\t\tInitial\tOptimized'
        output += '\nOverall summary'
        output += '\n\tPortfolio budget:\t%0.0f\t%0.0f' % (overallbud['init'], overallbud['opt'])
        output += '\n\tOutcome:\t%0.0f\t%0.0f' % (overallout['init'], overallout['opt'])
        for obkey in self.objectives['keys']:
            output += '\n\t' + self.objectives['keylabels'][obkey] + ':\t%0.0f\t%0.0f' % (overalloutcomesplit['num'+obkey]['init'], overalloutcomesplit['num'+obkey]['opt'])
        for caskey in self.objectives['cascadekeys']:
            output += '\n\t' + self.objectives['keylabels'][caskey] + ':\t%0.0f\t%0.0f' % (overalloutcomesplit[caskey]['init'], overalloutcomesplit[caskey]['opt'])
        
        
        ## Sort, then export
        projindices = argsort(projnames)
        for prj in projindices:
            output += '\n'
            output += '\n'
            output += '\n\t\tInitial\tOptimized'
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
    
    
    def export(self, filename=None, folder=None, verbose=2):
        ''' Export the results to Excel format '''
        
        fullpath = makefilepath(filename=filename, folder=folder, default=self.name+'-geospatial-results.xlsx', ext='xlsx')
        workbook = Workbook(fullpath)
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
        outstr = self.makeoutput(doprint=False) # Gather the results to export
        for line in outstr.split('\n'):
            outlist.append([])
            for cell in line.split('\t'):
                outlist[-1].append(str(cell)) # If unicode, doesn't work
        
        # Iterate over the data and write it out row by row.
        row, col = 0, 0
        for row in range(len(outlist)):
            for col in range(len(outlist[row])):
                thistxt = outlist[row][col]
                thisformat = 'plain'
                if col==0: thisformat = 'bold'
                tmptxt = thistxt.lower()
                for word in ['budget','outcome','allocation','initial','optimal','optimized','coverage']:
                    if tmptxt.find(word)>=0: thisformat = 'bold'
                if col in [2,3] and thisformat=='plain': thisformat = 'number'
                if thisformat=='number':thistxt = float(thistxt)
                worksheet.write(row, col, thistxt, formats[thisformat])
        
        worksheet.set_column(0, 3, colwidth) # Make wider
        workbook.close()
        
        printv('Results exported to %s' % fullpath, 2, verbose)
        return fullpath
        



   


def makegeospreadsheet(project=None, filename=None, folder=None, parsetname=None, copies=None, refyear=None, verbose=2, names=None):
    ''' 
    Create a geospatial spreadsheet template based on a project file.
    
    Arguments:
        project    -- base project to use
        filename   -- output filename
        folder     -- folder to use if not specified in filename
        parsetname -- parset to take projections from
        copies     -- optional argument specifying the number of regions
        refyear    -- the reference year for the projections for population size and prevalence estimates
        names      -- Optional list of names of regions; if supplied, len(names) overrides copies
    '''
    
    # Load a project file and set defaults
    if project is None: raise OptimaException('No project loaded.')
    if parsetname is None: parsetname = -1
    bestindex = 0 # Index of the best result -- usually 0 since [best, low, high]  
    fullpath = makefilepath(filename=filename, folder=folder, default=project.name+'-geospatial', ext='xlsx')
    
    # Try to extract results before 
    try:    results = project.parsets[parsetname].getresults()
    except: results = project.runsim(name=project.parsets[parsetname].name)
    
    # Handle copies
    if copies is None:
        if names is not None: copies = len(names)
        else:
            errormsg = 'You must supply either a number of copies or a list of region names'
            raise OptimaException(errormsg)
    copies = int(copies)
    
    # Handle names
    if names is None:
        names = []
        for row in range(copies):
            names.append('%s - region %i' % (project.name, row))
    
    # Handle reference year and other things
    if copies!=len(names):
        errormsg = 'Number of copies (%i) does not match number of named regions (%i)' % (copies, len(names))
        raise OptimaException(errormsg)
    refyear = int(refyear)
    if not refyear in [int(x) for x in results.tvec]:
        errormsg = "Input not within range of years used by aggregate project's last stored calibration."
        raise OptimaException(errormsg)
    else:
        refind = [int(x) for x in results.tvec].index(refyear)

    ## 2. Extract data needed from project (population names, program names...)
    workbook = Workbook(fullpath)
    wspopsize = workbook.add_worksheet('Population sizes')
    wsprev = workbook.add_worksheet('Population prevalence')
    plain = workbook.add_format({})
    num = workbook.add_format({'num_format':0x04})
    bold = workbook.add_format({'bold': True})
    orfmt = workbook.add_format({'bold': True, 'align':'center'})
    gold = workbook.add_format({'bg_color': '#ffef9d'})
    
    nprogs = len(project.data['pops']['short'])
    
    # Start with pop and prev data.
    maxcol = 0
    row, col = 0, 0
    for row in range(copies+1):
        if row != 0:
            wspopsize.write(row, col, names[row-1], bold)
            wsprev.write(row, col, "='Population sizes'!%s" % rc(row,col), bold)
        for popname in project.data['pops']['short']:
            col += 1
            if row == 0:
                wspopsize.write(row, col, popname, bold)
                wsprev.write(row, col, popname, bold)
            else:
                wspopsize.write(row, col, "=%s*%s/%s" % (rc(copies+2,col),rc(row,nprogs+2),rc(copies+2,nprogs+2)), num)

                # Prevalence scaling by function r/(r-1+1/x).
                # If n is intended district prevalence and d is calibrated national prevalence, then...
                # 'Unbound' (scaleup) ratio r is n(1-d)/(d(1-n)).
                # Variable x is calibrated national prevalence specific to pop group.
                natpopcell = rc(copies+2,col)
                disttotcell = rc(row,nprogs+2)
                nattotcell = rc(copies+2,nprogs+2)
                wsprev.write(row, col, "=(%s*(1-%s)/(%s*(1-%s)))/(%s*(1-%s)/(%s*(1-%s))-1+1/%s)" % (disttotcell,nattotcell,nattotcell,disttotcell,disttotcell,nattotcell,nattotcell,disttotcell,natpopcell), plain)

            maxcol = max(maxcol,col)
        col += 1
        if row > 0:
            wspopsize.write(row, col, "OR", orfmt)
            wsprev.write(row, col, "OR", orfmt)
        col += 1
        if row == 0:
            wspopsize.write(row, col, "Total (intended)", bold)
            wsprev.write(row, col, "Total (intended)", bold)
            for p in range(copies):
                wspopsize.write(row+1+p, col, None, gold)
                wsprev.write(row+1+p, col, None, gold)
        col += 1
        if row == 0:
            wspopsize.write(row, col, "Total (actual)", bold)
            wsprev.write(row, col, "Total (actual)", bold)
        else:
            wspopsize.write(row, col, "=SUM(%s:%s)" % (rc(row,1),rc(row,nprogs)), num)
            wsprev.write(row, col, "=SUMPRODUCT('Population sizes'!%s:%s,%s:%s)/'Population sizes'!%s" % (rc(row,1),rc(row,nprogs),rc(row,1),rc(row,nprogs),rc(row,col)), plain)
        maxcol = max(maxcol,col)
        col = 0
    
    # Just a check to make sure the sum and calibrated values match.
    # Using the last parset stored in project! Assuming it is the best calibration.
    row += 1              
    wspopsize.write(row, col, '---')
    wsprev.write(row, col, '---')
    row += 1
    wspopsize.write(row, col, 'Calibration %i' % refyear)
    wsprev.write(row, col, 'Calibration %i' % refyear)
    for popname in project.data['pops']['short']:
        col += 1
        wspopsize.write(row, col, results.main['popsize'].pops[bestindex][col-1][refind], num)
        wsprev.write(row, col, results.main['prev'].pops[bestindex][col-1][refind])
    col += 2
    wspopsize.write(row, col, results.main['popsize'].tot[bestindex][refind], num)
    wsprev.write(row, col, results.main['prev'].tot[bestindex][refind])
    col += 1
    wspopsize.write(row, col, "=SUM(%s:%s)" % (rc(row,1),rc(row,nprogs)), num)
    wsprev.write(row, col, "=SUMPRODUCT('Population sizes'!%s:%s,%s:%s)/'Population sizes'!%s" % (rc(row,1),rc(row,nprogs),rc(row,1),rc(row,nprogs),rc(row,col)))  
    col = 0
    
    row += 1
    wspopsize.write(row, col, 'District aggregate')
    wsprev.write(row, col, 'District aggregate')
    for popname in project.data['pops']['short']:
        col += 1
        wspopsize.write(row, col, '=SUM(%s:%s)' % (rc(1,col),rc(copies,col)), num)
        wsprev.write(row, col, "=SUMPRODUCT('Population sizes'!%s:%s,%s:%s)/'Population sizes'!%s" % (rc(1,col),rc(copies,col),rc(1,col),rc(copies,col),rc(row,col)))
    col += 2
    wspopsize.write(row, col, '=SUM(%s:%s)' % (rc(1,col),rc(copies,col)), num)
    wsprev.write(row, col, "=SUMPRODUCT('Population sizes'!%s:%s,%s:%s)/'Population sizes'!%s" % (rc(1,col),rc(copies,col),rc(1,col),rc(copies,col),rc(row,col)))
    col += 1
    wspopsize.write(row, col, "=SUM(%s:%s)" % (rc(row,1),rc(row,nprogs)), num)
    wsprev.write(row, col, "=SUMPRODUCT('Population sizes'!%s:%s,%s:%s)/'Population sizes'!%s" % (rc(row,1),rc(row,nprogs),rc(row,1),rc(row,nprogs),rc(row,col)))  
    col = 0
        
    colwidth = 20
    wsprev.set_column(0, maxcol, colwidth) # Make wider
    wspopsize.set_column(0, maxcol, colwidth) # Make wider
        
    # 3. Generate and save spreadsheet
    workbook.close()    
    printv('Geospatial spreadsheet template saved to "%s".' % fullpath, 2, verbose)

    return fullpath
    
    

# ONLY WORKS WITH VALUES IN THE TOTAL COLUMNS SO FAR!
def makegeoprojects(project=None, spreadsheetpath=None, destination=None, dosave=True, verbose=2):
    ''' Create a series of project files based on a seed file and a geospatial spreadsheet '''
    
    # 1. Get results and defaults
    if project is None or spreadsheetpath is None:
        errormsg = 'makegeoprojects requires a project and a spreadsheet path as inputs'
        raise OptimaException(errormsg)
    try:    results = project.parset().getresults()
    except: results = project.runsim()
    
    # 2. Load a spreadsheet file
    workbook = open_workbook(spreadsheetpath)
    wspopsize = workbook.sheet_by_name('Population sizes')
    wsprev = workbook.sheet_by_name('Population prevalence')
    
    # 3. Read the spreadsheet
    poplist = []
    for colindex in range(1,wspopsize.ncols-3): # Skip first column and last 3
        poplist.append(wspopsize.cell_value(0, colindex))
    npops = len(poplist)
    if npops!=project.data['npops']:
        errormsg = 'Selected project and selected spreadsheet are incompatible: %i vs. %i populations' % (npops, project.data['npops'])
        raise OptimaException(errormsg)
        
    districtlist = []
    popratio = odict()
    prevfactors = odict()
    plhivratio = odict()
    isdistricts = True
    for rowindex in range(wspopsize.nrows):
        if wspopsize.cell_value(rowindex, 0) == '---':
            isdistricts = False
        if isdistricts and rowindex > 0:
            districtlist.append(wspopsize.cell_value(rowindex, 0))
            
            # 'Actual' total ratios.
            if rowindex == 1:
                popratio['tot'] = []
                prevfactors['tot'] = []
                plhivratio['tot'] = []
            popratio['tot'].append(wspopsize.cell_value(rowindex, npops+3))
            prevfactors['tot'].append(wsprev.cell_value(rowindex, npops+3))
            plhivratio['tot'].append(wspopsize.cell_value(rowindex, npops+3)*wsprev.cell_value(rowindex, npops+3))
            
            # Population group ratios.
            for popid in range(npops):
                popname = poplist[popid]
                colindex = popid + 1
                if rowindex == 1:
                    popratio[popname] = []
                    prevfactors[popname] = []
                    plhivratio[popname] = []
                popratio[popname].append(wspopsize.cell_value(rowindex, colindex))
                prevfactors[popname].append(wsprev.cell_value(rowindex, colindex))
                plhivratio[popname].append(wspopsize.cell_value(rowindex, colindex)*wsprev.cell_value(rowindex, colindex))
    print('Districts:')
    print(districtlist)
    ndistricts = len(districtlist)
    
    # Workout the reference year for the spreadsheet for later 'datapoint inclusion'.
    refind = -1
    try:
        refyear = int(re.sub("[^0-9]", "", wspopsize.cell_value(ndistricts+2, 0)))         
        if refyear in [int(x) for x in project.data['years']]:
            refind = [int(x) for x in project.data['years']].index(refyear)
            print('Reference year %i found in data year range with index %i.' % (refyear,refind))
        else:
            print('Reference year %i not found in data year range %i-%i.' % (refyear,int(project.data['years'][0]),int(project.data['years'][-1])))
    except:
        OptimaException('Warning: Cannot determine calibration reference year for this spreadsheet.')
    
    # Important note. Calibration value will be used as the denominator! So ratios can sum to be different from 1.
    # This allows for 'incomplete' subdivisions, e.g. a country into 2 of 3 states.
    popdenom = wspopsize.cell_value(ndistricts+2, npops+3)
    popratio['tot'] = [x/popdenom for x in popratio['tot']]
    prevdenom = wsprev.cell_value(ndistricts+2, npops+3)
    prevfactors['tot'] = [x/prevdenom for x in prevfactors['tot']]
    plhivdenom = wspopsize.cell_value(ndistricts+2, npops+3)*wsprev.cell_value(ndistricts+2, npops+3)
    plhivratio['tot'] = [x/plhivdenom for x in plhivratio['tot']]        
    for popid in range(npops):
        colindex = popid + 1
        popname = poplist[popid]
        popdenom = wspopsize.cell_value(ndistricts+2, colindex)
        popratio[popname] = [x/popdenom for x in popratio[popname]]
        prevdenom = wsprev.cell_value(ndistricts+2, colindex)
        prevfactors[popname] = [x/prevdenom for x in prevfactors[popname]]
        plhivdenom = wspopsize.cell_value(ndistricts+2, colindex)*wsprev.cell_value(ndistricts+2, colindex)
        plhivratio[popname] = [x/plhivdenom for x in plhivratio[popname]]

    printv('Population ratio...', 4, verbose)
    printv(popratio, 4, verbose)                     # Proportions of national population split between districts.
    printv('Prevalence multiples...', 4, verbose)
    printv(prevfactors, 4, verbose)                   # Factors by which to multiply prevalence in a district.        
    printv('PLHIV ratio...', 4, verbose)
    printv(plhivratio, 4, verbose)                    # Proportions of PLHIV split between districts.
    
    # 4. Calibrate each project file according to the data entered for it in the spreadsheet
    projlist = []
    for c,districtname in enumerate(districtlist):
        newproject = dcp(project)
        newproject.restorelinks() # Ensure that the link objects have been updated
        newproject.name = districtname
        
        # Scale data        
        for popid in range(npops):
            popname = poplist[popid]
            for x in newproject.data['popsize']:
                x[popid] = [z*popratio[popname][c] for z in x[popid]]
            for x in newproject.data['hivprev']:
                x[popid] = [z*prevfactors[popname][c] for z in x[popid]]
        newproject.data['numtx'] = [[y*plhivratio['tot'][c] for y in x] for x in newproject.data['numtx']]
        newproject.data['numpmtct'] = [[y*plhivratio['tot'][c] for y in x] for x in newproject.data['numpmtct']]
        newproject.data['numost'] = [[y*plhivratio['tot'][c] for y in x] for x in newproject.data['numost']]
        
        # Scale calibration
        newproject.parsets[-1].pars['popsize'].m  *= popratio[popname][c] #TODO check change from ['popsize'].i[:] was appropriate
        newproject.parsets[-1].pars['initprev'].y[:] *= prevfactors[popname][c]
        newproject.parsets[-1].pars['numcirc'].y[:]  *= plhivratio['tot'][c]
        newproject.parsets[-1].pars['numtx'].y[:]    *= plhivratio['tot'][c]
        newproject.parsets[-1].pars['numpmtct'].y[:] *= plhivratio['tot'][c]
        newproject.parsets[-1].pars['numost'].y[:]   *= plhivratio['tot'][c]
        
        # Scale programs
        if len(project.progsets) > 0:
            for progid in newproject.progsets[-1].programs:
                program = newproject.progsets[-1].programs[progid]
                program.costcovdata['cost'] = plhivratio['tot'][c]*array(program.costcovdata['cost'],dtype=float)
                if program.costcovdata.get('coverage') is not None:
                    if not program.costcovdata['coverage'] == [None]:
                        program.costcovdata['coverage'] = plhivratio['tot'][c]*array(program.costcovdata['coverage'],dtype=float)
            
        datayears = len(newproject.data['years'])
        newproject.data['hivprev'] = [[[z*prevfactors[poplist[yind]][c] for z in y[0:datayears]] for yind, y in enumerate(x)] for x in results.main['prev'].pops]
#       newproject.autofit(name=psetname, orig=psetname, fitwhat=['force'], maxtime=None, maxiters=10, inds=None) # Run automatic fitting and update calibration
        newproject.runsim(newproject.parsets[-1].name) # Re-simulate autofit curves, but for old data.
        projlist.append(newproject)
    project.runsim(project.parsets[-1].name)
    
    # 5. Save each project file into the directory, or return the created projects
    if dosave:
        filepaths = []
        for subproject in projlist:
            fullpath = makefilepath(filename=subproject.name, folder=destination, ext='prj')
            filepaths.append(fullpath)
            subproject.filename = fullpath
            subproject.save()
        return filepaths
    else:
        return projlist