import optima as op
import sciris as sc

fn2 = 'test2.prj'

P = sc.loadobj(fn2)

P.runsim()
op.pygui(P)
