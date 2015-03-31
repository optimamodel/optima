from numpy import array

def migrate(D):
    # Change inhomogenities
    for s in xrange(len(D['F'])):
        if 'inhomo' not in D['F'][s].keys():
            D['F'][s]['inhomo'] = (array(D['F'][s]['force'])*0).tolist()
    return D
