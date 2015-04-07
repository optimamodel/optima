def migrate(D):
    # Restructure programs
    if 'programs' in D and isinstance (D['programs'], dict):
        newprograms = []
        for program in D['programs']:
            neweffects = []
            for effect in D['programs'][program]['effects']:
                neweffect = {'paramtype':effect[0][0], \
                             'param':effect[0][1], \
                             'popname':effect[1][0] }
                if len(effect)==3: neweffect['coparams'] = effect[2]
                if len(effect)==4: neweffect['convertedcoparams'] = effect[3]
                if len(effect)==5: neweffect['convertedccoparams'] = effect[4]
                neweffects.append(neweffect)
            newprogram = {'name':program, \
                          'nonhivdalys':D['programs'][program]['nonhivdalys'], \
                          'convertedccparams':D['programs'][program]['convertedccparams'], \
                          'ccparams':D['programs'][program]['ccparams'], \
                          'effects':neweffects}
            newprograms.append(newprogram)
<<<<<<< HEAD:server/src/versioning/002_add_programs.py
            
=======

>>>>>>> develop:server/src/versioning/003_add_programs.py
        # Reorder programs
        neworder = []
        for i in range(D['G']['nprogs']):
            neworder.append([p['name'] for p in newprograms].index(D['data']['meta']['progs']['short'][i]))
        reorderednewprograms = [newprograms[i] for i in neworder]
<<<<<<< HEAD:server/src/versioning/002_add_programs.py
            
=======

>>>>>>> develop:server/src/versioning/003_add_programs.py
        D['programs'] = reorderednewprograms

    return D
