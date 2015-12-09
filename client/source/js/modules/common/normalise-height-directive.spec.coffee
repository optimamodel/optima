define ['angular-mocks', 'Source/modules/common/normalise-height-directive'], ->
  describe 'normaliseHeight directive in app.common.normalise-height', ->
    element = null
    scope = null

    beforeEach ->
      module 'app.common.normalise-height'

      inject ($rootScope, $compile) ->
        scope = $rootScope.$new()
        scope.value = true

        html = '<div style="height: 300px" normalise-height></div>'
        html += '<div style="height: 100px" normalise-height></div>'

        # Compile a piece of HTML containing the directive
        element = $compile(html)(scope)
        # Evaluate expressions
        scope.$digest()

    it 'should normalise the height of both elements to 300px', ->
      expect($(element[0]).height()).toBe(300)
      expect($(element[1]).height()).toBe(300)

    it 'should react & normalise the height on the "draw" event', ->
      $(element[1]).height(400)
      $(element[1]).trigger('draw', [{height: 400}])
      scope.$digest()
      expect($(element[0]).height()).toBe(400)
      expect($(element[1]).height()).toBe(400)
