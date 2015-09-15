import optima.ccocs as ccocs
import optima
# cost_coverage = ccocs.cc_scaleup(defaults.program['ccparams']['parameters'])
# coverage_outcome = ccocs.cc_scaleup(defaults.program['coparams'][0])


# codata = [2.0, 0.0]
# c = ccocs.co_linear(codata)
# c.plot(1,draw=True)

#r = optima.Project.load_json('tests/regions/projects/georgia_working.json')
#r.save('asdf.bin')
r = optima.Project.load('asdf.bin')

r.programsets[0].programs[3].plot()
print r.programsets[0].programs[5].coverage_outcome['Overall']
#r.programsets[0].programs[1].plot_single('FSW')
# r.programsets[0].programs[1].plot_single('FSW','condomcom',cco=True)