"""
Create a good test project

Version: 2016feb08
"""
import optima as op

projname = 'exercise_complete.prj'

P = op.loadobj(projname)
op.saveobj(projname, P)