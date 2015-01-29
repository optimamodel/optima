// ProjectOpenController deals with loading and removing projects

define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectOpenController',
    function ($scope, $http, $upload, activeProject, projects, modalService, fileUpload, UserManager) {

    $scope.projects = _.map(projects.projects, function(project){
      project.creation_time = Date.parse(project.creation_time);
      project.data_upload_time = Date.parse(project.data_upload_time);
      return project;
    });

    /**
     * Opens an existing project using `name`
     *
     * Alerts the user if it cannot do it.
     */
    $scope.open = function (name, id) {
      $http.get('/api/project/open/' + id)
        .success(function (response) {
          if (response && response.status === 'NOK') {
            alert(response.reason);
            return;
          }
          activeProject.setActiveProjectFor(name, id, UserManager.data);
          window.location = '/';
        });
    };


    /**
     * Copy an existing project using `name`
     *
     * Prompts for the new project name.
     */
    $scope.copy = function(name, id) {
      modalService.showPrompt(
        "Copy project?",
        "New project name",
        function(newName) {
          $http.post('/api/project/copy/' + id + '?to=' + newName)
            .success(function (response) {
              window.location.reload();
            });
        }
      );
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

    $scope.setData = function (name, id, file) {
      var message = 'Warning: This will overwrite ALL data in the project ' + name + '. Are you sure you wish to continue?';
      modalService.confirm(
        function (){ fileUpload.uploadDataSpreadsheet($scope, file, '/api/project/data/'+id, false); },
        function (){},
        'Yes, overwrite data',
        'No',
        message,
        'Upload data'
      );
    };

    $scope.preSetData = function(name, id) {
      angular
        .element('<input type=\'file\'>')
        .change(function(event){
        $scope.setData(name, id, event.target.files[0]);
      }).click();
    };

    /**
     * Removes the project
     *
     * If the removed project is the active one it will reset it alerts the user
     * in case of failure.
     */
    var removeNoQuestionsAsked = function (name, id, index) {
      $http.delete('/api/project/delete/' + id)
        .success(function (response) {
          $scope.projects = _($scope.projects).filter(function (item) {
            return item.name != name;
          });
          activeProject.ifActiveResetFor(name, id, UserManager.data);
        });
    };

    /**
     * Opens a modal window to ask the user for confirmation to remove the project and
     * removes the project if the user confirms.
     * Closes it without further action otherwise.
     */
    $scope.remove = function ($event, name, id, index) {
      if ($event) { $event.preventDefault(); }
      var message = 'Are you sure you want to permanently remove project "' + name + '"?';
      modalService.confirm(
        function (){ removeNoQuestionsAsked(name, id, index); },
        function (){},
        'Yes, remove this project',
        'No',
        message,
        'Remove project'
      );
    };
  });

});
