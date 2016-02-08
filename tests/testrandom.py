"""
Version:
"""

import optima as op
P = op.Project(spreadsheet='example.xlsx')
op.pygui(P.results[0])