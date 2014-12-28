define ['angular-mocks', 'Source/modules/d3-charts/d3-charts-service',
  'jquery'], ->
  describe 'd3Charts service in app.d3-charts', ->

    d3ChartsService = null

    beforeEach ->
      module 'app.d3-charts'

      inject (d3Charts) ->
        d3ChartsService = d3Charts

    describe 'createSvg', ->

      createSvg = ->
        wrapper = document.createElement "div"
        dimensions = {width: 100, height: 120}
        margins = {left: 20, top: 10, right: 10, bottom: 5}
        d3ChartsService.createSvg wrapper, dimensions, margins
        $(wrapper).find('svg')

      it 'should create an svg element', ->
        $svg = createSvg()
        expect($svg.length).toBe(1)

      it 'should create an svg element with the provided dimensions', ->
        $svg = createSvg()
        expect($svg.attr('width')).toBe('100')
        expect($svg.attr('height')).toBe('120')

      it 'should create an svg element with the provided margin', ->
        $svg = createSvg()
        expect($svg.attr('style')).toBe('padding:10px 10px 5px 20px')

    describe 'adaptOptions()', ->

      describe 'if graph title and legend is set', ->
        options = null

        beforeEach ->
          options = {
            title: 'Foo',
            legend: ['Foo'],
            height: 100,
            margin: {
              top: 10
            }
          }

        it 'should set hasTitle boolean', ->
          options = d3ChartsService.adaptOptions(options)
          expect(options.hasTitle).toBe(true)

        it 'should set hasLegend boolean', ->
          options = d3ChartsService.adaptOptions(options)
          expect(options.hasLegend).toBe(true)

        it 'should increase margin-top', ->
          options = d3ChartsService.adaptOptions(options)
          expect(options.margin.top).toBe(40)

        it 'should increase height', ->
          options = d3ChartsService.adaptOptions(options)
          expect(options.height).toBe(130)

      describe 'legend transformation', ->

        it 'should translate legend from array of strings to array of objects', ->
          options = d3ChartsService.adaptOptions({
            legend: ['foo', 'bar']
            margin: { top: 10 }
          })
          expect(options.legend[1].title).toBe('bar')

        it 'should attach color if customColor option provided', ->
          options = d3ChartsService.adaptOptions({
            legend: ['foo', 'bar']
            margin: { top: 10 }
            linesStyle: ['a', 'b', 'c', 'd']
          })
          expect(options.legend[0].color).toBe('a')
          expect(options.legend[1].color).toBe('b')
