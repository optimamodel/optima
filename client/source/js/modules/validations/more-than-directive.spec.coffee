define ['angular-mocks', 'Source/modules/validations/more-than-directive'], ->
  describe 'lessThan directive in app.validations.more-than', ->
    element = null
    scope = null

    beforeEach ->
      module 'app.validations.more-than'

      inject ($rootScope, $compile) ->
        scope = $rootScope.$new()
        scope.lowValue = 5
        scope.highValue = 10

        html = '<form name="myForm">'
        html += '<input type="number" name="myInput" ng-model="highValue" more-than="lowValue">'
        html += '</form>'

        # Compile a piece of HTML containing the directive
        element = $compile(html)(scope)
        # Evaluate expressions
        scope.$digest()

    it 'should set the input to valid for proper values', ->
      expect(scope.myForm.myInput.$valid).toBeTruthy()
      expect(scope.myForm.$valid).toBeTruthy()

    it 'should set the input to invalid if the lowValue is changed to be higher', ->
      scope.lowValue = 11
      scope.$digest()
      expect(scope.myForm.myInput.$valid).toBeFalsy()
      expect(scope.myForm.$valid).toBeFalsy()

    it 'should set the input to invalid if the highValue is changed to lower', ->
      scope.highValue = 0
      scope.$digest()
      expect(scope.myForm.myInput.$valid).toBeFalsy()
      expect(scope.myForm.$valid).toBeFalsy()
