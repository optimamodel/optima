define ['angular-mocks', 'Source/modules/model/program-set/program-set-modal-service',
  'Source/modules/ui/modal/modal-service'], ->
  describe 'programSetModalService service in app.model', ->

    psModalService = null

    beforeEach ->
      module 'app.model'
      module 'app.ui.modal'

      inject (programSetModalService) ->
        psModalService = programSetModalService

    describe 'programSetModalService', ->

      it 'should have openProgramSetModal defined', ->
        expect(psModalService.openProgramSetModal).toBeDefined()
