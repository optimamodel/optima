"""
MAKETEMPLATE

Version: 2014oct28
"""

def makeproject(projectname='example', numpopgroups=6, numprograms=8, startyear=2000, endyear=2015):
    # Create project -- TODO: check if an existing project exists and don't overwrite it
    from scipy.io import savemat
    savemat(projectname+'.mat',{'projectname':projectname})
    
    # Make an Excel template and then prompt the user to save it
    from maketemplate import maketemplate
    templatename = maketemplate(projectname, numpopgroups, numprograms, startyear, endyear)
    
    return templatename