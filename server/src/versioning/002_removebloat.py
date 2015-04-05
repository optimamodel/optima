def migrate(D):
    # Remove bloat from scenarios
    if 'scens' in D.keys():
        for i, s in enumerate(D['scens']):
            try:
                s.pop('M')
                s.pop('S')
                s.pop('R')
                print('Removed bloat from scenario %d' % i)
            except:
                print('Removing bloat from scenario %d failed' % i)

    # Remove bloat from optimizations
    if 'optimizations' in D.keys():
        for i, o in enumerate(D['optimizations']):
            try:
                o['result'].pop('debug')
                print('Removed bloat from optimization %d' % i)
            except:
                print('Removing bloat from optimization %d failed' % i)
    return D
