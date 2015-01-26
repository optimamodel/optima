define ['Source/modules/d3-charts/scale-helpers'], (scaleHelpers) ->

  describe 'scale-helpers in app.d3-charts', ->

    describe 'evaluateTickFormat', ->

      it 'should choose a precesion of 3 decimal points for a range smaller than 0.01', ->
        expect(scaleHelpers.evaluateTickFormat(0, 0.009)).toBe('.3f')
        expect(scaleHelpers.evaluateTickFormat(0.1, 0.1002)).toBe('.3f')
        expect(scaleHelpers.evaluateTickFormat(-0.001, -0.002)).toBe('.3f')

      it 'should choose a precesion of 2 decimal points for a range smaller than 1', ->
        expect(scaleHelpers.evaluateTickFormat(0, 0.9)).toBe('.2f')
        expect(scaleHelpers.evaluateTickFormat(0.1, 0.2)).toBe('.2f')
        expect(scaleHelpers.evaluateTickFormat(-0.1, -0.2)).toBe('.2f')

      it 'should choose a precesion of 1 decimal points for a range smaller than 10', ->
        expect(scaleHelpers.evaluateTickFormat(0, 9)).toBe('.1f')
        expect(scaleHelpers.evaluateTickFormat(3, 4)).toBe('.1f')
        expect(scaleHelpers.evaluateTickFormat(-1, -2)).toBe('.1f')

      it 'should choose a precesion of 0 decimal points for a range between 10 & 10,000', ->
        expect(scaleHelpers.evaluateTickFormat(0, 11)).toBe('.0f')
        expect(scaleHelpers.evaluateTickFormat(0, 2014)).toBe('.0f')
        expect(scaleHelpers.evaluateTickFormat(-1, -20)).toBe('.0f')

      it 'should choose a precesion of 0 decimal points for a range between 10,000 & 100,000', ->
        expect(scaleHelpers.evaluateTickFormat(0, 10001)).toBe(',.0f')
        expect(scaleHelpers.evaluateTickFormat(1000, 100000)).toBe(',.0f')
        expect(scaleHelpers.evaluateTickFormat(-1, -20000)).toBe(',.0f')

      it 'should choose a custom formating for a range above 100,000', ->
        expect(scaleHelpers.evaluateTickFormat(0, 100001)).toBe('custom')
        expect(scaleHelpers.evaluateTickFormat(1000, 200000)).toBe('custom')
        expect(scaleHelpers.evaluateTickFormat(-1, -200000)).toBe('custom')

    describe 'customTickFormat', ->

      it 'should format a number by d3\'s internal formatting function', ->
        expect(scaleHelpers.customTickFormat(100, ',.2f')).toBe('100.00')
        expect(scaleHelpers.customTickFormat(2.654, ',.1f')).toBe('2.7')

      it 'should format a number by the custom optima formatting', ->
        expect(scaleHelpers.customTickFormat(200000, 'custom')).toBe('200K')
        expect(scaleHelpers.customTickFormat(300000000, 'custom')).toBe('300m')
        expect(scaleHelpers.customTickFormat(400000000000, 'custom')).toBe('400bn')

    describe 'flexCeil', ->

      it 'should round up to integer & for smaller than 1 to the first non zero decimal', ->
        expect(scaleHelpers.flexCeil(100)).toBe(100)
        expect(scaleHelpers.flexCeil(1.2)).toBe(2)
        expect(scaleHelpers.flexCeil(0.2)).toBe(0.2)
        expect(scaleHelpers.flexCeil(0.023)).toBe(0.03)
        expect(scaleHelpers.flexCeil(0.000654)).toBe(0.0007)
