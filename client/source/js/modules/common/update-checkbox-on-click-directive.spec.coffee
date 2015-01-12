define ['angular-mocks', 'Source/modules/common/update-checkbox-on-click-directive'], ->
  describe 'updateCheckboxOnClick directive in app.common.update-checkbox-on-click', ->
    element = null
    scope = null

    beforeEach ->
      module 'app.common.update-checkbox-on-click'

      inject ($rootScope, $compile) ->
        scope = $rootScope.$new()
        scope.value = true

        html = '<div update-checkbox-on-click>'
        html += '<input type="checkbox" ng-model="value">'
        html += '</div>'

        # Compile a piece of HTML containing the directive
        element = $compile(html)(scope)
        # Evaluate expressions
        scope.$digest()

    it 'should toggle the bound model value if clicked on the outer element', ->
      $checkbox = $(element).find('input[type=checkbox]')
      clickEvent = $.Event("click", { target: element, currentTarget: element })
      $(element).trigger(clickEvent)
      scope.$digest()
      expect(scope.value).toBeFalsy()

    it 'should toggle the bound model value if clicked on the checkbox', ->
      $checkbox = $(element).find('input[type=checkbox]')
      clickEvent = $.Event("click", {
        target: $checkbox[0],
        currentTarget: $checkbox[0]
      })
      $checkbox.trigger(clickEvent)
      scope.$digest()
      expect(scope.value).toBeFalsy()
