define(['./module'], function (module) {

  module.directive('menu', function ($state, UserManager, fileUpload, activeProject, modalService, $state) {
    return {
      restrict: 'A',
      scope: {
        settings: '= menu'
      },
      templateUrl: function() {
        return 'js/modules/ui/menu/menu.html';
      },
      controller: [
        '$scope',
        function ($scope) {
          $scope.isAdmin = UserManager.isAdmin;

          $scope.uploadSpreadsheet = function() {
            if(activeProject.isSet()){
              angular
                .element('<input type="file">')
                .change(function (event) {
                  fileUpload.uploadDataSpreadsheet($scope, event.target.files[0]);
                })
                .click();
            } else {
              modalService.inform(
                function (){ },
                'Okay',
                'Create or open a project first.',
                'Cannot proceed'
              );
            }
          };

          $scope.goIfProjectActive = function(stateName) {
            if(activeProject.isSet()){
              $state.go(stateName);
            } else {
              modalService.inform(
                function (){ },
                'Okay',
                'Create or open a project first.',
                'Cannot proceed'
              );
            }
          }
        }
      ]
    };
  });
});
