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
        margins = {left: 20, top: 10}
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
        $g = $svg.find('g')
        expect($g.attr('transform')).toBe('translate(20,10)')
