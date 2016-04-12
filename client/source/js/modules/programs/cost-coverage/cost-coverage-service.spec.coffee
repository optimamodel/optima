define ['angular-mocks', 'Source/modules/programs/cost-coverage/cost-coverage-service'], ->
  describe 'costCoverageHelpers service in app.programs', ->

    helpers = null

    beforeEach ->
      module 'app.programs'

      inject (costCoverageHelpers) ->
        helpers = costCoverageHelpers

    describe 'convertFromPercent()', ->

      it 'should return a number divided by 100', ->
        expect(helpers.convertFromPercent(60)).toBe(0.6)
        expect(helpers.convertFromPercent(2)).toBe(0.02)
        expect(helpers.convertFromPercent(-33)).toBe(-0.33)

      it 'should return NaN for anything else then a number', ->
        expect(helpers.convertFromPercent("60")).toBeNaN()
        expect(helpers.convertFromPercent(undefined)).toBeNaN()
        expect(helpers.convertFromPercent(null)).toBeNaN()
