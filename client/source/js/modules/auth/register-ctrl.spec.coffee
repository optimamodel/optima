###
  You can also write tests in JavaScript, see home-ctrl.spec.js
###

define ['angular-mocks', 'Source/modules/auth/register-ctrl'], ->
  describe 'RegisterController in app.auth', ->
    scope = null
    subject = null

    beforeEach ->
      module 'app.auth'
      module 'ui.router'

      inject ($rootScope, $controller) ->
        scope = $rootScope.$new()
        subject = $controller 'RegisterController', { $scope: scope, $window: null, User: null }

      describe 'check if controller is on it\'s place', ->
        it 'should have loaded the subject', ->
          expect(subject).toBeDefined()

      describe 'check if scope is also on it\'s place', ->
        it 'should test scope to be defined', ->
          expect(scope).toBeDefined()

      describe 'check if scope has error and register defined', ->
        it 'should test scope to be defined', ->
        expect(scope.error).toBeDefined()
        expect(scope.register).toBeDefined()
