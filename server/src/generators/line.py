
def generatedata(endyear):
    result = []
    for p in range(2000,endyear):
        x = float(p)
        y = (float(p)-1990)**(0.5)
        result.append({'x': x, 'y': y})
    return result
