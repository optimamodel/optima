define ['angular-mocks', 'Source/modules/project-set/program-set/program-set-modal-ctrl','Source/modules/project/project-api-service',
  'Source/modules/project-set/program-set/program-set-modal-service', 'Source/modules/ui/modal/modal-service',
  'Source/modules/user-manager/index', 'Source/modules/common/active-project-service'], ->
  describe 'ProgramSetModalController in app.model', ->
    scope = null
    subject = null

    beforeEach ->
      module 'ui.router'
      module 'app.project'
      module 'app.project-set'
      module 'app.user-manager'
      module 'app.ui.modal'
      module 'app.active-project'

      inject ($rootScope, $controller) ->
        scope = $rootScope.$new()
        subject = $controller 'ProgramSetModalController', { $scope: scope, $window: null, program: {name: 'abc'}, populations: null, programList: null, availableParameters: null, $modalInstance: null }

    it 'should have loaded the subject', ->
      expect(subject).toBeDefined()

    it 'should test scope to be defined', ->
      expect(scope).toBeDefined()
