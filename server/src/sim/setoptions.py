def setoptions(opt=None, **kwargs):
    """
    Set the options for running the simulation.
    
    Version: 2014nov23 by cliffk
    """
    
    from bunch import Bunch as struct
    from numpy import arange
    
    # If no options structure is fed in
    if not(isinstance(opt,dict)): 
        opt = struct() # If existing options structure isn't provided, create it
        opt.startyear = kwargs.get('startyear',2000) # First year of simulation to run
        opt.endyear = kwargs.get('endyear',2030) # Final year of simulation to run
        opt.dt = 0.1 # Timestep
        opt.nsims = kwargs.get('nsims',5) # Number of simulations to store for purposes of uncertainty
        opt.quantiles = [0.5, 0.25, 0.75] # Quantiles to return
        opt.growth = 0.03 # Default population growth rate
        opt.disc = 0.05 # Economic discounting rate
        opt.turnofftrans = float("inf") # Turn off transmissions, set to trivial as default - a negative value will break out of the main model loop, whilst a postive value will continue to run the model but not calculate new infections
    
    # Replace any keys that exist
    for key, value in kwargs.iteritems():
        if key in opt.keys():
            opt[key] = value # Update value
    
    opt.tvec = arange(opt.startyear, opt.endyear+opt.dt, opt.dt) # Recalculate time vector
    opt.npts = len(opt.tvec) # Number of time points
    
    return opt