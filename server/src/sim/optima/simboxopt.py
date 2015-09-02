from simbox import SimBox
from simbudget import SimBudget

import defaults
from copy import deepcopy

# A container just for Sims with budgets. (No hard-coded restriction on multiple unoptimised SimBudgets exist, but may be considered lest things 'break'.)
# Note: I'm starting to think it best that there is only ever on SimBudget under focus, i.e. the latest one.
#       SimBoxOpt should always return data from the last SimBudget in its list.
class SimBoxOpt(SimBox):
    def __init__(self,name,region):
        SimBox.__init__(self,name,region)
        
    def load_dict(self, simboxdict):
        SimBox.load_dict(self,simboxdict)
       
    def todict(self):
        simboxdict = SimBox.todict(self)
        simboxdict['type'] = 'SimBoxOpt'    # Overwrites SimBox type.
        
        return simboxdict
        
    # Overwrites the standard Sim create method for SimBudgets. Only one per SimBoxOpt can be unoptimised in general.
    def createsim(self, simname, budget = [], forcecreate = False):
        if not forcecreate:
            for sim in self.simlist:
                if not sim.isoptimised():
                    print('Optimisation containers can only contain one unoptimised simulation!')
                    return None
        print('Preparing new budget simulation for optimisation container %s...' % self.name)
        newsim = SimBudget(simname, self.getregion(), budget)
        newsim.initialise()
        self.simlist.append(newsim)
        return newsim
        
    # Overwrites normal SimBox method so that SimBudget is not only run, but optimised, with the results copied to a new SimBudget.
    def runallsims(self, forcerun = False, forceopt = False):
        numsims = len(self.simlist)        
        
        # The loop only optimises unoptimised SimBudgets that were already in the simlist before new ones were added.
        # This assumes the first 'numsims' amount of SimBudgets were originally in the list. Deleting and shuffling positions will cause problems!
        for x in xrange(numsims):
            sim = self.simlist[x]
            if forcerun or not sim.isprocessed():
                sim.run()
            if sim.isprocessed() and (forceopt or not sim.isoptimised()):
                self.optimise(sim, makenew = True)

            
    # Currently just optimises simulation according to defaults. As in... fixed initial budget!
    def optimise(self, origsim, makenew = True, inputmaxiters = defaults.maxiters, inputtimelimit = defaults.timelimit):
        r = self.getregion()

        from optimize import optimize
        
        tempD = dict()
        tempD['data'] = deepcopy(r.data)
        tempD['data']['origalloc'] = deepcopy(origsim.alloc)
        tempD['opt'] = deepcopy(r.options)
        tempD['programs'] = deepcopy(r.metadata['programs'])
        tempD['G'] = deepcopy(r.metadata)
        tempD['P'] = deepcopy(origsim.parsdata)
        for key in origsim.getcalibration().keys():     # Quick fix since calibration change. But is it safe...?
            tempD['P'][key] = origsim.getcalibration()[key] 
        tempD['M'] = deepcopy(origsim.parsmodel)
        tempD['F'] = deepcopy(origsim.parsfitted)
        tempD['R'] = deepcopy(origsim.debug['results'])      # Does this do anything?
        tempD['plot'] = dict()
        
        tempD['S'] = deepcopy(origsim.debug['structure'])     # Need to run simulation before optimisation!
        optimize(tempD, maxiters = inputmaxiters, timelimit = inputtimelimit, returnresult = True),        
        
        origsim.plotdataopt = tempD['plot']['optim'][-1]       # What's this -1 business about?
        
        # Let's try returning these rather than storing them...
#        optalloc = self.plotdataopt['alloc'][-1]['piedata']
        optobj = tempD['objective'][-1]
#        resultopt = tempD['result']['debug']    # VERY temporary. Only until we understand how to regenerate parameters from new allocations.
#        newbudget = tempD['result']['debug']['newbudget']
#        print optalloc
#        print newbudget
        
        # If makenew is on, the optimisation results will be initialised in a new SimBudget.
        
#        # Optimisation returns an allocation and a (hopefully corresponding) objective function value.
#        # It also returns a resulting data structure (that we'll hopefully remove the need for eventually).
#        # Finally, it returns a boolean for whether a new SimBudget should be made.
#        return (optalloc, optobj, resultopt, makenew)
        
        # Maybe should avoid hardcoding the timevarying bit, but it works for default optimisation.
        from timevarying import timevarying          
        
        optalloc = tempD['optalloc']
        optbudget = timevarying(optalloc, ntimepm = 1, nprogs = len(optalloc), tvec = self.getregion().options['partvec'])        

        if makenew:
            origsim.optimised = True
            
            print('Converting optimisation results into a new budget simulation...')
            newsim = self.createsim(origsim.getname() + ' Optimised', optbudget, forcecreate = True)
            newsim.run()
        
        return (optbudget, optobj, makenew)
        
    # Calculates objective values for certain multiplications of an alloc's variable costs (passed in as list of factors).
    # The idea is to spline a cost-effectiveness curve across several budget totals.
    # Note: We don't care about the allocations in detail. This is just a function between totals and the objective.
    def calculateeffectivenesscurve(self, sim, factors):
        curralloc = sim.alloc
        
        totallocs = []
        objarr = []
        timelimit = defaults.timelimit
#        timelimit = 1.0
        
        # Work out which programs don't have an effect and are thus fixed costs (e.g. admin).
        # These will be ignored when testing different allocations.
        fixedtrue = [1.0]*(len(curralloc))
        for i in xrange(len(curralloc)):
            if len(self.getregion().metadata['programs'][i]['effects']): fixedtrue[i] = 0.0
        
        for factor in factors:
            try:
                print('Testing budget allocation multiplier of %f.' % factor)
                sim.alloc = [curralloc[i]*(factor+(1-factor)*fixedtrue[i]) for i in xrange(len(curralloc))]
                betterbudget, betterobj, a = self.optimise(sim, makenew = False, inputtimelimit = timelimit)
                
                betteralloc = [alloclist[0] for alloclist in betterbudget]
                
                objarr.append(betterobj)
                totallocs.append(sum(betteralloc))
            except:
                print('Multiplying pertinent budget allocation values by %f failed.' % factor)
            
        sim.alloc = curralloc
        
        # Remember that total alloc includes fixed costs (e.g admin)!
        return (totallocs, objarr)
            

    
    # A custom built plotting function to roughly mirror legacy 'viewoptimresults'.
    def viewoptimresults(self, plotasbar = False):
        atleastoneplot = False
        for sim in self.simlist:
            if sim.isinitialised():
                atleastoneplot = True
                
        if not atleastoneplot:
            print('There is no optimisation data in this simulation container to plot.')
        else:
            r = self.region()
            
            from matplotlib.pylab import figure, subplot, plot, pie, bar, title, legend, xticks, ylabel, show
            from gridcolormap import gridcolormap
            from matplotlib import gridspec
        
            nprograms = len(r.data['origalloc'])
            colors = gridcolormap(nprograms)
            
            if plotasbar:
                figure(figsize=(len(self.simlist)*2+4,nprograms/2))
                gs = gridspec.GridSpec(1, 2, width_ratios=[len(self.simlist), 2]) 
                ind = xrange(len(self.simlist))
                width = 0.8       # the width of the bars: can also be len(x) sequence
                
                subplot(gs[0])
                bar(ind, [sim.alloc[-1] for sim in self.simlist], width, color=colors[-1])
                for p in xrange(2,nprograms+1):
                    bar(ind, [sim.alloc[-p] for sim in self.simlist], width, color=colors[-p], bottom=[sum(sim.alloc[1-p:]) for sim in self.simlist])
                xticks([index+width/2.0 for index in ind], [sim.getname() for sim in self.simlist])
                ylabel('Budget Allocation ($)')
                
                subplot(gs[1])
                for prog in xrange(nprograms): plot(0, 0, linewidth=3, color=colors[prog])
                legend(r.data['meta']['progs']['short'])
            else:
                figure(figsize=(12,4*(len(self.simlist)/3+1)))
                c = 0
                for p in xrange(len(self.simlist)):
                    sim = self.simlist[p]
                    if sim.isprocessed():
                        subplot(len(self.simlist)/3+1,3,p-c+1)
                        pie(sim.alloc, colors=colors, labels=r.data['meta']['progs']['short'])
                        title(sim.getname())
                    else:
                        c += 1
            show()
#        subplot(2,1,2)
#        plot(O['outcome']['xdata'], O['outcome']['ydata'])
#        xlabel(O['outcome']['xlabel'])
#        ylabel(O['outcome']['ylabel'])
#        title(O['outcome']['title'])
    
    # Special printing method for SimBoxOpt to take into account whether a Sim was already optimised.
    def printsimlist(self, assubsubset = False):
        # Prints with long arrow formats if assubsubset is true. Otherwise uses short arrows.        
        if assubsubset:
            if len(self.simlist) > 0:
                for sim in self.simlist:
                    print('   --> %s%s' % (sim.getname(), (" (initialised)" if not sim.isprocessed() else " (simulated + %s)" %
                                             ("further optimisable" if not sim.isoptimised() else "already optimised"))))
        else:
            if len(self.simlist) == 0:
                print(' --> No simulations are currently stored in container %s.' % self.getname())
            else:
                for sim in self.simlist:
                    print(' --> %s%s' % (sim.getname(), (" (initialised)" if not sim.isprocessed() else " (simulated + %s)" %
                                             ("further optimisable" if not sim.isoptimised() else "already optimised"))))



    # Scales the variable costs of an alloc so that the sum of the alloc equals newtotal.
    # Note: Can this be fused with the scaling on the Region level...?
    def scalealloctototal(self, sim, newtotal):
        curralloc = sim.alloc
        
        # Work out which programs don't have an effect and are thus fixed costs (e.g. admin).
        # These will be ignored when testing different allocations.
        fixedtrue = [1.0]*(len(curralloc))
        for i in xrange(len(curralloc)):
            if len(self.getregion().metadata['programs'][i]['effects']): fixedtrue[i] = 0.0
                
        # Extract the fixed costs from scaling.
        fixedtotal = sum([curralloc[i]*fixedtrue[i] for i in xrange(len(curralloc))])
        vartotal = sum([curralloc[i]*(1.0-fixedtrue[i]) for i in xrange(len(curralloc))])
        scaledtotal = newtotal - fixedtotal
        
        # Deal with a couple of possible errors.
        if scaledtotal < 0:
            print('Warning: You are attempting to generate an allocation for a budget total that is smaller than the sum of relevant fixed costs!')
            print('Continuing with the assumption that all non-fixed program allocations are zero.')
            print('This may invalidate certain analyses such as GPA.')
            scaledtotal = 0
        try:
            factor = scaledtotal/vartotal
        except:
            print("Possible 'divide by zero' error.")
            curralloc[0] = scaledtotal      # Shove all the budget into the first program.
        
        # Updates the alloc of this SimBudget according to the scaled values.
        sim.alloc = [curralloc[i]*(factor+(1-factor)*fixedtrue[i]) for i in xrange(len(curralloc))]
        
    

    def __repr__(self):
        return "SimBoxOpt %s ('%s')" % (self.uuid[0:8],self.name)