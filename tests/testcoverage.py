

from optima.programs import Costcov
import numpy


def testcostcoverage():

    # Setup a cost-coverage object
    costcovfn = Costcov()

    # Add parameters for a cost-coverage curve in a budget year
    costcovfn.addccopar({
        'saturation': (0.75,0.85),
        't': 2013.0,
        'unitcost': (30,40)
    })

    # Add/remove more parameters
    costcovfn.addccopar({
        'saturation': (0.45,0.65),
        't': 2015.0,
        'unitcost': (25,35)
    })
    costcovfn.rmccopar(2015)

    costcovfn.addccopar({'t': 2016.0, 'unitcost': (25, 35)})
    costcovfn.addccopar({'t': 2016.0, 'unitcost': (20, 30)}, overwrite=True)

    costcovfn.addccopar({'t': 2017.0, 'unitcost': (30, 35)})

    # Calculate the coverages, given budgets and different years
    budgets = [0, 50000, 1000000]
    years = [2013, 2015, 2017]
    popsize = 2e9

    coverages = costcovfn.evaluate(
        x=budgets, t=years, popsize=popsize, bounds=None, toplot=False)
    targetcoverages = [1.00000000e-03, 1.76470588e+03, 3.13712488e+04]
    assert numpy.allclose(coverages, targetcoverages, atol=1e-05)

    # Check the conversion back from coverages into the budget
    # convertedbudgets = costcovfn.evaluate(x=coverages, t=years, rtol=1e-05, atol=1e-05)
    # assert numpy.allclose(convertedbudgets, budgets, atol=1e-05)

