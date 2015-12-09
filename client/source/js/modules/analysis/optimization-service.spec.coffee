define ['angular-mocks', 'Source/modules/analysis/optimization-service', 'jquery'], ->
  describe 'optimizationHelpers service in app.analysis', ->

    helpers = null
    scopeParameters = null

    beforeEach ->
      module 'app.analysis'

      inject (optimizationHelpers) ->
        helpers = optimizationHelpers
        scopeParameters = {
          objectives: {
            money: {
              objectives: {}
            }
          }
        }

    describe 'toRequestParameters', ->

      it 'should add timelimit only if it is provided', ->
        parameters = helpers.toRequestParameters(scopeParameters, 'test', 3600)
        expect(parameters.timelimit).toBe(3600)
        parameters = helpers.toRequestParameters(scopeParameters, 'test')
        expect(parameters.timelimit).toBeUndefined()

      it 'should add name', ->
        parameters = helpers.toRequestParameters(scopeParameters, 'testMe')
        expect(parameters.name).toBe('testMe')

      it 'should divide percentage values by 100', ->
        scopeParameters.objectives.money.objectives = {
          dalys: {by: 88.3}
        }
        parameters = helpers.toRequestParameters(scopeParameters, 'testMe')
        expect(parameters.objectives.money.objectives.dalys.by).toBe(0.883)

    describe 'toScopeObjectives', ->

      it 'should multiply percentage values by 100', ->
        responseObjectives = {
          money: {
            objectives: {
              dalys: {by: 0.283}
            }
          }
        }
        objectives = helpers.toScopeObjectives(responseObjectives)
        expect(objectives.money.objectives.dalys.by).toBe(28.30)
