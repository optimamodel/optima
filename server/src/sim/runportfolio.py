"""
RUNPORTFOLIO

Procedure to run this file:
1. Go to ui.optimamodel.com and download the .json files to investigate.
2. Place them in the projects folder. This should be a subfolder of the one that stores this script!
3. Press F5 to run (or from the Run menu, select Run).
4. Choose a name for your portfolio and then follow the ensuing instructions.
5. Load as many projects as you want.
5. ...
6. Profit?

For developers:
- Each loaded project has its own individually populated data structure D.
- Any typical processes you wish to apply to individual Ds should be coded as a method of Project class (projectclass.py).
- However, ALL processes should be initiated at the Portfolio class level (portfolioclass.py) and propagate down.
  'Portfolio' should ideally be hooked up as the interface for the front-end.
  For example, want to apply 'optimize' to the nth loaded project within the portfolio?
  Code something like 'def optimize(self,n,parameters)', which should in turn call 'self.projectlist[n-1].optimise(parameters)'.
- Likewise, any processes to apply across multiple Ds should be coded while iterating through a subset of Portfolio's projectlist.
  This includes the geo-prioritisation algorithm but can be extended.

Version: 2015may29
"""
import add_optima_paths
import defaults

print('WELCOME TO OPTIMA')

from portfolio import Portfolio

portfolioname = raw_input('Please enter a name for your portfolio: ')

currentportfolio = Portfolio(portfolioname)
currentportfolio.run()

