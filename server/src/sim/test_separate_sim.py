import optima,liboptima
from timevarying import timevarying

r = optima.Project.load_json('./projects/zambia-with-new-testing-removed-null-prog.json')
s = optima.Sim('test',r)
s.run()
liboptima.save(s.todict(),'tempfile')

s2 = optima.Sim.fromdict(liboptima.load('tempfile'))
optima.plot(s2)



