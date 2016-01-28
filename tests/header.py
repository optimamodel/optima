"""
TESTHEADER

The header repeated from each of the tests. Load it with

exec(open('header.py').read())

...super secure, I know.

Version: 2016jan27
"""


from optima import tic, toc, blank, pd # analysis:ignore

if 'doplot' not in locals(): doplot = True

def done(t=0):
    print('Done.')
    toc(t)
    blank()

blank()
print('Running tests:')
for i,test in enumerate(tests): print(('%i.  '+test) % (i+1))
blank()
T = tic()