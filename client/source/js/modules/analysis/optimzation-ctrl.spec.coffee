###
  You can also write tests in JavaScript, see questions-ctrl.spec.js
###

define ['angular-mocks', 'Source/modules/analysis/optimization-ctrl'], ->
  describe 'AnalysisOptimizationController in app.analysis', ->
    scope = null
    subject = null

    beforeEach ->
      module 'app.analysis'

      inject ($rootScope, $controller) ->
        meta = {
          "pops": {
            "client": [ 0 ],
            "female": [ 0 ],
            "injects": [ 0 ],
            "long": [ "Men who have sex with men" ],
            "male": [ 1 ],
            "sexmen": [ 0 ],
            "sexwomen": [ 1 ],
            "sexworker": [ 0 ],
            "short": [ "MSM" ]
          },
          "progs": {
            "currentbudget": [ 154000.00000000003 ],
            "long": [ "Social and behavior change communication" ],
            "saturating": [ 1 ],
            "short": [ "SBCC" ]
          }
        }

        scope = $rootScope.$new()
        subject = $controller 'AnalysisOptimizationController', {
          $scope: scope
          meta: meta
          modalService: {}
        }

    describe 'yearIsRequired()', ->

      it 'should be false if funding is not defined', ->
        expect(scope.yearIsRequired()).toBeFalsy()

      it 'should be true if funding is set to variable', ->
        scope.params.objectives.funding = 'variable'
        expect(scope.yearIsRequired()).toBeTruthy()

    describe 'updateYearRange()', ->

      beforeEach ->
        scope.params.objectives.funding = 'variable';

      it 'should reset outcome, yearLoop & yearCols', ->
        scope.updateYearRange()

        expect(scope.params.objectives.outcome.variable).toEqual({})
        expect(scope.yearLoop).toEqual([])
        expect(scope.yearCols).toEqual([])

      it 'should parse the start & end date & create yearLoop & yearCols', ->
        scope.params.objectives.year = { start: "2015", end: "2020" }
        scope.updateYearRange()

        expect(scope.params.objectives.outcome.variable).toEqual({})
        expect(scope.yearLoop).toEqual([ { year : 2015 }, { year : 2016 },
          { year : 2017 }, { year : 2018 }, { year : 2019 }, { year : 2020 } ])
        expect(scope.yearCols).toEqual([ { start : 0, end : 5 },
          { start : 5, end : 10 } ])
