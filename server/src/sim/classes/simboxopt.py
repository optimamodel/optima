# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 21:32:57 2015

@author: David Kedziora
"""

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
        
    # Overwrites the standard Sim create method. This is where budget data would be attached.
    def createsim(self, simname):
        sim = None
        if len(self.simlist) > 0:
            print('Optimisation containers can only contain one initial simulation!')
        else:
            print('Preparing new budget simulation for optimisation container %s...' % self.name)
            self.simlist.append(SimBudget(simname+'-initial',self.getregion()))
            self.simlist[-1].initialise()
            sim = self.simlist[-1]
        return sim
        
    # Overwrites normal SimBox method so that SimBudget is not only run, but optimised, with the results (possibly) copied to a new SimBudget.
    def runallsims(self, forcerun = False, forceopt = False):
        tempsim = None
        makenew = False
        
        for sim in self.simlist:
            if forcerun or not sim.isprocessed():
                sim.run()
            if sim.isprocessed() and (forceopt or not sim.isoptimised()):
                (optbudget, optobj, makenew) = self.optimise(sim)
                tempsim = sim
                
        # Generates a new SimBudget from the last Sim that was optimised in the list, but only when the loop has ended and if requested.
        if makenew:
#            self.createsimopt(tempsim, optalloc, optobj, resultopt)
            self.createsimopt(tempsim, optbudget)
            
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
        if makenew:
            origsim.optimised = True
        
#        # Optimisation returns an allocation and a (hopefully corresponding) objective function value.
#        # It also returns a resulting data structure (that we'll hopefully remove the need for eventually).
#        # Finally, it returns a boolean for whether a new SimBudget should be made.
#        return (optalloc, optobj, resultopt, makenew)
        
        # Maybe should avoid hardcoding the timevarying bit, but it works for default optimisation.
        from timevarying import timevarying          
        
        optalloc = tempD['optalloc']
        optbudget = timevarying(optalloc, ntimepm = 1, nprogs = len(optalloc), tvec = self.getregion().options['partvec'])        
        
        return (optbudget, optobj, makenew)
            
    # This creates a duplicate SimBudget to 'sim', except with optimised 'G', 'M', 'F', 'S' from sim.resultopt.
    # As an optimised version of the previous SimBudget, it will also be automatically processed, to get plotdata.
    def createsimopt(self, sim, optbudget):
        if not sim == None:
            print('Converting optimisation results into a new budget simulation...')
            self.simlist.append(SimBudget(sim.getname(), self.getregion(), optbudget))
            
            # The copy can't be completely deep or shallow, so we load the new SimBudget with a developer-made method.
#            self.simlist[-1].specialoptload(sim, optalloc, optobj, resultopt)
            self.simlist[-1].run()
    
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

    
    # Complicated method that ends up with an additional stored SimBudget optimised for a different budget total.
    # Note: Read comments carefully. This is a messy process. Deepcopy used for safety.
    #       Also, it may be worth stripping the legacy code of processes at some stage so that the procedure is transparent in OOP form.
    def createsimoptgpa(self, newtotal):
        from copy import deepcopy
        remsim = deepcopy(self.simlist[-1])                 # Memorises latest SimBudget in SimBoxOpt.
        self.simlist[-1].scalealloctototal(newtotal)        # Overwrites the alloc of this SimBudget with a new one that exemplifies a particular budget total (e.g. from GPA).
        self.runallsims()                                   # Optimises the SimBudget with the new alloc. (Presumably, the optimize function reinitialises all model parameters for this alloc...)
        self.simlist[-2] = deepcopy(remsim)                 # Having created a new SimBudget, reverts the old one.
        self.simlist[-2].optimised = True                   # But locks it so that it cannot be further optimised.
        self.simlist[-1].optimised = True                   # Likewise locks the new SimBudget.
        self.runallsims(forcerun = True)                    # Processes both the old and new SimBudget (as well as any previous SimBudgets in the SimBoxOpt).


    def __repr__(self):
        return "SimBoxOpt %s ('%s')" % (self.uuid[0:8],self.name)