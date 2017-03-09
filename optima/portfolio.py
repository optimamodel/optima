from optima import OptimaException, gitinfo, tic, toc, odict, getdate, today, uuid, dcp, objrepr, printv, findinds, saveobj, loadproj, promotetolist # Import utilities
from optima import version, defaultobjectives, Project, pchip, getfilelist, batchtools
from numpy import arange, argsort, zeros, nonzero, linspace, log, exp, inf, argmax, array
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

    def __init__(self, name='default', objectives=None, projects=None, gaoptims=None):
        ''' Initialize the portfolio '''

        ## Set name
        self.name = name

        ## Define the structure sets
        self.projects = odict()
        self.objectives = objectives
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
            printv('Added project %s to portfolio %s' % (project.name, self.name), 2, verbose)
        return None
    
    
    def addfolder(self, folder=None, replace=True, verbose=2):
        ''' Add a folder of projects to a portfolio '''
        filelist = getfilelist(folder, 'prj')
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
        
    def runGA(self, grandtotal=None, objectives=None, boclist=None, npts=None, maxiters=None, maxtime=None, reoptimize=True, mc=None, batch=True, maxload=None, interval=None, doprint=True, export=False, outfile=None, verbose=2):
        ''' Complete geospatial analysis process applied to portfolio for a set of objectives '''
        
        GAstart = tic()
        
        # Check inputs
        if npts is None: npts = 2000 # The number of points to calculate along each BOC
        if mc is None: mc = 0 # Do not use MC by default
        if objectives is not None: self.objectives = objectives # Store objectives, if supplied
        
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
        if reoptimize: 
            resultpairs = batchtools.reoptimizeprojects(projects=self.projects, objectives=objectives, maxtime=maxtime, maxiters=maxiters, mc=mc, batch=batch, maxload=maxload, interval=interval, verbose=verbose)
            self.results = resultpairs
        # Tidy up
        if doprint and self.results: self.makeoutput(doprint=doprint, verbose=verbose)
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
    
    
    def makeoutput(self, doprint=True, verbose=2):
        ''' Just displays results related to the GA run '''
        if doprint: printv('Printing results...', 2, verbose)
        
        # Keys for initial and optimized
        iokeys = ['init', 'opt'] 
        
        # Initialize to zero
        projnames = []
        projbudgets = []
        projcov = []
        projoutcomes = []
        projoutcomesplit = []
        
        overallbud = odict() # Overall budget
        overallout = odict() # Overall outcomes
        for io in iokeys:
            overallbud[io] = 0
            overallout[io] = 0
        
        overalloutcomesplit = odict()
        for obkey in self.objectives['keys']:
            overalloutcomesplit['num'+obkey] = odict()
            for io in iokeys:
                overalloutcomesplit['num'+obkey][io] = 0
        
        for k,key in enumerate(self.results.keys()):
            # Figure out which indices to use
            projectname = self.results[key]['init'].projectinfo['name']
            projnames.append(projectname)
            projbudgets.append(odict())
            projoutcomes.append(odict())
            projoutcomesplit.append(odict())
            projcov.append(odict())
            tvector, initial, final, indices, alloc, outcome, sumalloc = [odict() for o in range(7)] # Allocate all dicts
            for io in iokeys:
                tvector[io]  = self.results[key][io].tvec # WARNING, can differ between initial and optimized!
                initial[io]  = findinds(tvector[io], self.objectives['start'])
                final[io]    = findinds(tvector[io], self.objectives['end'])
                indices[io]  = arange(initial[io], final[io])
                alloc[io]    = self.results[key][io].budget
                outcome[io]  = self.results[key][io].outcome 
                sumalloc[io] = alloc[io][:].sum() # Should be a budget odict that we're summing
                overallbud[io] += sumalloc[io]
                overallout[io] += outcome[io]
                projbudgets[k][io]  = alloc[io]
                projoutcomes[k][io] = outcome[io]
                
                tmppars = self.results[key][io].parset
                tmpprog = self.results[key][io].progset
                tmpcov = tmpprog.getprogcoverage(alloc[io], self.objectives['start'], parset=tmppars)
                projcov[k][io]  = tmpcov
                
                projoutcomesplit[k][io] = odict()
                for obkey in self.objectives['keys']:
                    projoutcomesplit[k][io]['num'+obkey] = self.results[key][io].main['num'+obkey].tot[0][indices[io]].sum()     # Again, current and optimal should be same for 0 second optimisation, but being explicit.
                    overalloutcomesplit['num'+obkey][io] += projoutcomesplit[k][io]['num'+obkey]
                
        ## Actually create the output
        output = ''
        output += 'Geospatial analysis results: minimize outcomes from %i to %i' % (self.objectives['start'], self.objectives['end'])
        output += '\n\n'
        output += '\n\t\tInitial\tOptimal'
        output += '\nOverall summary'
        output += '\n\tPortfolio budget:\t%0.0f\t%0.0f' % (overallbud['init'], overallbud['opt'])
        output += '\n\tOutcome:\t%0.0f\t%0.0f' % (overallout['init'], overallout['opt'])
        for obkey in self.objectives['keys']:
            output += '\n\t' + self.objectives['keylabels'][obkey] + ':\t%0.0f\t%0.0f' % (overalloutcomesplit['num'+obkey]['init'], overalloutcomesplit['num'+obkey]['opt'])
        
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
    
    
    def export(self, filename=None, verbose=2):
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
        outstr = self.makeoutput(doprint=False) # Gather the results to export
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
        
        printv('Results exported to %s' % filename, 2, verbose)
        return None
        



   


