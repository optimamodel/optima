define ['angular-mocks', 'Source/modules/programs/cost-coverage/cost-coverage-ctrl'], ->
  describe 'ModelCostCoverageController in app.programs', ->
    scope = null
    subject = null

    beforeEach ->
      module 'app.programs'

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
