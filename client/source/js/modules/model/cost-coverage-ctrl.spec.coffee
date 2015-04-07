define ['angular-mocks', 'Source/modules/model/cost-coverage-ctrl'], ->
  describe 'ModelCostCoverageController in app.model', ->
    scope = null
    subject = null

    beforeEach ->
      module 'app.model'

      inject ($rootScope, $controller, costCoverageHelpers) ->
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
            "short": [ "SBCC" ]
          }
        }

        scope = $rootScope.$new()
        subject = $controller 'ModelCostCoverageController', {
          $scope: scope
          meta: meta
          modalService: {}
          info: {}
          programs: [],
          costCoverageHelpers: costCoverageHelpers
        }

    # move to cost-coverage-service spec
    # describe 'convertFromPercent()', ->
    #
    #   it 'should return a number divided by 100', ->
    #     expect(scope.convertFromPercent(60)).toBe(0.6)
    #     expect(scope.convertFromPercent(2)).toBe(0.02)
    #     expect(scope.convertFromPercent(-33)).toBe(-0.33)
    #
    #   it 'should return NaN for anything else then a number', ->
    #     expect(scope.convertFromPercent("60")).toBeNaN()
    #     expect(scope.convertFromPercent(undefined)).toBeNaN()
    #     expect(scope.convertFromPercent(null)).toBeNaN()
