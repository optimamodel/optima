import sys
sys.path.append('../tests')
import add_optima_paths

import ccocs
import defaults

# cost_coverage = ccocs.cc_scaleup(defaults.program['ccparams']['parameters'])
# coverage_outcome = ccocs.cc_scaleup(defaults.program['coparams'][0])


codata = [2.0, 0.0]
coverage_outcome = ccocs.co_linear(codata)
print coverage_outcome.evaluate(5)