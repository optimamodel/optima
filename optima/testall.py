# -*- coding: utf-8 -*-
"""
TESTALL

Run all tests except 'testworkflow', 'testgui'

Version: 2016jan02 by cliffk
"""

tests = [
'testutils',
'testproject',
'testprograms',
'testmodel',
'testmodalities',
'testscenarios',
]

failed = []
for test in tests:
    try:
        exec('import '+test)
    except:
        failed.append(test)


if len(failed):
    print('The following tests failed :(')
    for fail in failed: print('  %s' % fail)
else:
    print('All %i tests passed!!! You are the best!!' % len(tests))