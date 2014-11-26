def setoptions(opt=None, **kwargs):
    """
    Set the options for running the simulation.
    
    Version: 2014nov23 by cliffk
    """
    
    from bunch import Bunch as struct
    from numpy import arange
    
    # If no options structure is fed in, 
    if opt==None: 
        opt = struct() # If existing options structure isn't provided, create it
        opt.startyear = 2000 # First year of simulation to run
        opt.endyear = 2030 # Final year of simulation to run
        opt.dt = 0.1 # Timestep
        opt.nsims = 1 # Number of simulations to store for purposes of uncertainty
        opt.quantiles = [0.5, 0.25, 0.75] # Quantiles to return
        opt.growth = 0.03 # Default population growth rate
        opt.disc = 0.05 # Economic discounting rate
    
    for key, value in kwargs.iteritems():
        if key in ['startyear', 'endyear', 'dt', 'nsims', 'quantiles']:
            opt[key] = value # Update value
        elif key=='opt':
            pass # Don't do anything with this
        else:
            print('WARNING, option %s not recognized' % key)
    
    opt.tvec = arange(opt.startyear, opt.endyear+opt.dt, opt.dt) # Recalculate time vector
    
    return opt