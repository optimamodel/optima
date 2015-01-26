define ['Source/modules/d3-charts/stacked-bar-chart'], (StackedBarChart) ->

  describe 'stacked-bar-chart in app.d3-charts', ->

    describe 'new StackedBarChart', ->

      createChart = (data) ->
        chartSize = {width: 200, height: 200}
        colors = [ '__light-blue', '__blue', '__violet', '__green']
        new StackedBarChart(undefined, chartSize, data, colors)

      it 'should return a StackedBarChart instance', ->
        data = [
          [2001, [4, 7]]
          [2002, [9, 2]]
        ]
        chart = createChart(data)
        expect(chart).toBeDefined()
        expect(chart.draw).toBeDefined()
        expect(chart.yMax).toBeDefined()
        expect(chart.axisScales).toBeDefined()

      describe 'yMax', ->

        it 'should return the highest point of all bars', ->
          data = [
            [2001, [4, 9]]
            [2002, [9, 2]]
          ]
          chart = createChart(data)
          expect(chart.yMax()).toBe(13)

      describe 'axisScales', ->

        it 'should return an object with x & y functions', ->
          data = [
            [2001, [4, 9]]
            [2002, [9, 2]]
          ]
          chart = createChart(data)
          expect(typeof chart.axisScales().x).toBe('function')
          expect(typeof chart.axisScales().y).toBe('function')
