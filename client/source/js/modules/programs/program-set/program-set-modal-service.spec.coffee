define ['angular-mocks', 'Source/modules/programs/program-set/program-set-modal-service',
  'Source/modules/ui/modal/modal-service'], ->
  describe 'programSetModalService service in app.programs', ->

    psModalService = null

    beforeEach ->
      module 'app.programs'
      module 'app.ui.modal'

      inject (programSetModalService) ->
        psModalService = programSetModalService

    describe 'programSetModalService', ->

      it 'should have openProgramSetModal defined', ->
        expect(psModalService.openProgramSetModal).toBeDefined()
