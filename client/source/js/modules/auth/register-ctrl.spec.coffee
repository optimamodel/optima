define ['angular-mocks', 'Source/modules/auth/register-ctrl'], ->
  describe 'RegisterController in app.auth', ->
    scope = null
    subject = null

    beforeEach ->
      module 'ui.router'
      module 'app.auth'

      inject ($rootScope, $controller) ->
        scope = $rootScope.$new()
        subject = $controller 'RegisterController', { $scope: scope, $window: null, User: null }

    it 'should have loaded the subject', ->
      expect(subject).toBeDefined()

    it 'should test scope to be defined', ->
      expect(scope).toBeDefined()

    it 'should test error and register defined to be defined', ->
      expect(scope.error).toBe(false)
      expect(scope.register).toBeDefined()
