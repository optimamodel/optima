def setoptions(opt=None, **kwargs):
    """
    Set the options for running the simulation.
    
    Version: 2015feb03 by cliffk
    """
    
    from bunch import Bunch as struct
    from numpy import arange
    
    # If no options structure is fed in
    if not(isinstance(opt,dict)): 
        opt = dict() # If existing options structure isn't provided, create it
        opt['parstartyear'] = kwargs.get('parstartyear', 2000) # First year of parameter time series
        opt['parendyear'] = kwargs.get('parendyear', 2030) # Final year of parameter time series -- maximum time period for this project
        opt['simstartyear'] = kwargs.get('simstartyear', 2000) # First year of simulation to run
        opt['simendyear'] = kwargs.get('simendyear', 2030) # Final year of simulation to run
        opt['dt'] = 0.2 # Timestep
        opt['nsims'] = kwargs.get('nsims', 5) # Number of simulations to store for purposes of uncertainty
        opt['quantiles'] = [0.5, 0.25, 0.75] # Quantiles to return
        opt['growth'] = 0.0 # Default population growth rate
        opt['disc'] = 0.05 # Economic discounting rate
        opt['turnofftrans'] = float(1e9) # Turn off transmissions, set to trivial as default - a negative value will break out of the main model loop, whilst a postive value will continue to run the model but not calculate new infections
    
    # Replace any keys that exist
    for key, value in kwargs.iteritems():
        if key in opt.keys():
            opt[key] = value # Update value
    
    opt['partvec'] = arange(opt['parstartyear'], opt['parendyear']+opt['dt'], opt['dt']) # Recalculate time vector
    opt['simtvec'] = arange(max(opt['parstartyear'],opt['simstartyear']), min(opt['parendyear'],opt['simendyear'])+opt['dt'], opt['dt']) # Recalculate time vector using whatever's smaller, regular years or sim years
    
    return opt
