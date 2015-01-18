from glob import glob
files = glob('test_*.py')
for thisfile in files:
   print('''
   \n\n\n\n\n\n\n\n\n
   ###################################################
   IMPORTING %s
   ###################################################
   ''' % thisfile)
   execfile(thisfile)
