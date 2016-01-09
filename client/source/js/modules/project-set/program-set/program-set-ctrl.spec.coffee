define ['angular-mocks', 'Source/modules/model/program-set/program-set-ctrl', 'Source/modules/project/project-api-service',
  'Source/modules/model/program-set/program-set-modal-service', 'Source/modules/ui/modal/modal-service',
  'Source/modules/user-manager/index', 'Source/modules/common/active-project-service'], ->
  describe 'ProgramSetController in app.model', ->
    scope = null
    subject = null

    beforeEach ->
      module 'ui.router'
      module 'app.project'
      module 'app.model'
      module 'app.user-manager'
      module 'app.ui.modal'
      module 'app.active-project'

      inject ($rootScope, $controller) ->
        scope = $rootScope.$new()
        subject = $controller 'ProgramSetController', { $scope: scope, $window: null, User: null, predefined: {data: {}}, availableParameters: null }

    it 'should have loaded the subject', ->
      expect(subject).toBeDefined()

    it 'should test scope to be defined', ->
      expect(scope).toBeDefined()
