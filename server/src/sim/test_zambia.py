import optima,liboptima
from timevarying import timevarying

r = optima.Project.load_json('./projects/zambia-with-new-testing-removed-null-prog.json')
s = optima.Sim('test',r)
optima.plot(s)
