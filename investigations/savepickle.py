import optima as op

fn1 = 'test.prj'
fn2 = 'test2.prj'

P = op.loadproj(fn1)

P.created = str(P.created)
P.modified = str(P.modified)
P.spreadsheetdate = str(P.spreadsheetdate)
P.data['meta']['date'] = str(P.data['meta']['date'])
for parset in P.parsets.values():
    parset.created = str(parset.created)
    parset.modified = str(parset.modified)

#P.parsets = op.odict()
P.progsets = op.odict()
P.scens = op.odict()
P.optims = op.odict()
P.results = op.odict()

P.save(fn2)
