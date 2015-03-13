define(['./module'], function (module) {

  return module.directive('editableInput', function () {
    return {
      replace: true,
      templateUrl: 'js/modules/ui/editable/editable-input.html',
      scope: {
        field: '=editableInput',
        placeholder: '@',
        callback: '=onSave'
      },
      link: function (scope, element) {
        var textInput = element.find('input').focus();
        scope.mode = 'view';

        scope.switchToEdit = function (event) {
          if (event) {
            event.preventDefault();
          }

          scope.mode = 'edit';

          setTimeout(function () {
            textInput.focus();
          }, 0);
        };

        scope.switchToView = function (event) {
          if (event) {
            event.preventDefault();
          }

          scope.mode = 'view';


          scope.callback && scope.callback();
        };
      }
    };
  });
});
