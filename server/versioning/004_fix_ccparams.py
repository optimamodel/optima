def migrate(D):
    # Restructure ccparams in programs
    if 'programs' in D and isinstance (D['programs'], list):
      for program in D['programs']:
        if isinstance(program['ccparams'], list):
          ccparams = program['ccparams']
          ccparams.extend([None]*(9-len(ccparams)))
          newccparams = {'saturation': ccparams[0], 
          'coveragelower': ccparams[1], 
          'coverageupper':ccparams[2], 
          'funding':ccparams[3], 
          'scaleup':ccparams[4], 
          'nonhivdalys':ccparams[5], 
          'xupperlim':ccparams[6], 
          'cpibaseyear':ccparams[7], 
          'perperson':ccparams[8]}
          program['ccparams'] = newccparams

    return D
