
def generatedata(numpoints):
    result = []
    for p in range(numpoints):
        x = float(p)
        y = float(p)**(0.5)
        result.append({'x': x, 'y': y})
    return result
