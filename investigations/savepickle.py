import optima as op

fn1 = 'test.prj'
fn2 = 'test2.prj'

P = op.loadproj(fn1)

P.created = str(P.created)
P.modified = str(P.modified)
P.spreadsheetdate = str(P.spreadsheetdate)
P.data['meta']['date'] = str(P.data['meta']['date'])
for structlist in [P.parsets, P.progsets, P.optims, P.results]:
    for item in structlist.values():
        item.created = str(item.created)
        item.modified = str(item.modified)

#P.parsets = op.odict()
#P.progsets = op.odict()
#P.scens = op.odict()
#P.optims = op.odict()
#P.results = op.odict()

P.save(fn2)
