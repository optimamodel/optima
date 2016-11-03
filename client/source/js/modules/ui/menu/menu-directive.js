define(['./module'], function (module) {

  module.directive(
    'menu',
    function(
      $state, UserManager, fileUpload, activeProject,
      modalService, $http) {

        return {

          restrict: 'A',

          scope: {settings: '= menu'},

          templateUrl: function() {
            return 'js/modules/ui/menu/menu.html';
          },

          controller: [
            '$scope',
            function ($scope) {

              $scope.state = $state.current;
              console.log('$state', $state);

              $scope.isAdmin = UserManager.isAdmin;

              $scope.getState = function() {
                return $state.current.name;
              };

              $scope.isState = function(testName) {
                return $scope.getState().indexOf(testName) !== -1;
              };

              $scope.goIfProjectActive = function(stateName) {
                if(activeProject.isSet()){
                  console.log('current state', $state.current.name, '->', stateName);
                  $state.go(stateName);
                } else {
                  modalService.inform(
                    function () {},
                    'Okay',
                    'Create or open a project first.',
                    'Cannot proceed'
                  );
                }
              };

              $scope.logout = function() {
                $http.get('/api/user/logout').
                  success(function() {
                    window.location.reload();
                  });
              };

            }
          ]
        };
  });
});
