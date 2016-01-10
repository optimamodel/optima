define ['angular-mocks', 'Source/modules/project-set/program-set/program-set-modal-service',
  'Source/modules/ui/modal/modal-service'], ->
  describe 'programSetModalService service in app.project-set', ->

    psModalService = null

    beforeEach ->
      module 'app.project-set'
      module 'app.ui.modal'

      inject (programSetModalService) ->
        psModalService = programSetModalService

    describe 'programSetModalService', ->

      it 'should have openProgramSetModal defined', ->
        expect(psModalService.openProgramSetModal).toBeDefined()
