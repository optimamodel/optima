define ['Source/modules/common/svg-to-png', 'jquery'], (svgToPng, $) ->

  describe 'svg-to-png in app.common', ->

    describe 'parsePixel', ->

      it 'should return 34 for "34px"', ->
        expect(svgToPng.parsePixel("34px")).toBe(34)

      it 'should return 12.6842 for "12.6842px"', ->
        expect(svgToPng.parsePixel("12.6842px")).toBe(12.6842)

      it 'should return 0 for "not a number"', ->
        expect(svgToPng.parsePixel("not a number")).toBe(0)

      it 'should return 0 for ""', ->
        expect(svgToPng.parsePixel("")).toBe(0)

    describe 'scalePaddingStyle', ->

      it 'should scale the padding values', ->
        svg = svgToPng.createSvg(40, 40, 2, "padding: 10px 5px 3px 20px")
        expectedStyle = 'padding-top: 20px; padding-right: 10px;'
        expectedStyle += ' padding-bottom: 6px; padding-left: 40px'
        expect(svgToPng.scalePaddingStyle(svg, 2)).toBe(expectedStyle)
