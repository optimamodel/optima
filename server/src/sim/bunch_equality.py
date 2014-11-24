from bunch import Bunch as struct

a = struct()
b = struct()
a.a = 1
print a != b
b.a = 1
print a == b
