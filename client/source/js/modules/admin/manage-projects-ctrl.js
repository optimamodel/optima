define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('AdminManageProjectsController', function ($scope, $http, info, projects, users, activeProject, UserManager, modalService) {
    $scope.users = users.data.users;
    $scope.users = _.compact(_.map(_(projects.data.projects).groupBy(function (p) {return p.user_id;}), function (projects, userId) {
      var user = _.findWhere($scope.users, {id: parseInt(userId)});
      return user.email===UserManager.data.email ? undefined :{
        projects: projects,
        data: user
      };
    }));

    /**
     * Regenerates workbook for the given project `name`
     * Alerts the user if it cannot do it.
     *
     */
    $scope.workbook = function (name, id) {
      // read that this is the universal method which should work everywhere in
      // http://stackoverflow.com/questions/24080018/download-file-from-a-webapi-method-using-angularjs
      window.open('/api/project/workbook/' + id, '_blank', '');
    };

    /**
     * Opens to edit an existing project using `name` in /project/create screen
     *
     * Alerts the user if it cannot do it.
     */
    $scope.edit = function (name, id) {
      $http.get('/api/project/open/' + id)
        .success(function (response) {
          activeProject.setActiveProjectFor(name, id, UserManager.data);
          window.location = '/#/project/edit';
        });
    };

    /**
     * Opens an existing project using `name`
     *
     * Alerts the user if it cannot do it.
     */
    $scope.open = function (name, id) {
      $http.get('/api/project/open/' + id)
        .success(function (response) {
          activeProject.setActiveProjectFor(name, id, UserManager.data);
          window.location = '/';
        });
    };

    /**
     * Opens a modal window to ask the user for confirmation to remove the project and
     * removes the project if the user confirms.
     * Closes it without further action otherwise.
     */
    $scope.remove = function ($event, user, name, id, index) {
      if ($event) {
        $event.preventDefault();
      }
      var message = 'Are you sure you want to permanently remove project "' + name + '"?';
      modalService.confirm(
        function () {
          removeNoQuestionsAsked(user, name, id, index);
        },
        function () {
        },
        'Yes, remove this project',
        'No',
        message,
        'Remove project'
      );
    };

    /**
     * Gets the data for the given project `name` as <name>.json  file
     */
    $scope.getData = function (name, id) {
      $http({url:'/api/project/data/'+ id,
        method:'GET',
        headers: {'Content-type': 'application/json'},
        responseType:'arraybuffer'})
        .success(function (response, status, headers, config) {
          var blob = new Blob([response], { type: 'application/json' });
          saveAs(blob, (name + '.json'));
        });
    };

    /**
     * Removes the project
     *
     * If the removed project is the active one it will reset it alerts the user
     * in case of failure.
     */
    var removeNoQuestionsAsked = function (user, name, id, index) {
      $http.delete('/api/project/delete/' + id)
        .success(function (response) {
          if (response && response.status === 'NOK') {
            modalService.inform(undefined, undefined, response.reason);
            return;
          }

          user.projects = _(user.projects).filter(function (item) {
            return item.id != id;
          });
          $scope.projects = _($scope.projects).filter(function (item) {
            return item.id != id;
          });

          activeProject.ifActiveResetFor(name, id, UserManager.data);
        });
    };
  });
});
