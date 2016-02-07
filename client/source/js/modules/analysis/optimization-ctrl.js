define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  /**
   * Defines & validates objectives, parameters & constraints to run, display &
   * save optimization results.
   */
  module.controller('AnalysisOptimizationController', function ($scope, $http, $modal, modalService, activeProject) {

    if (!activeProject.data.has_data) {
      modalService.inform(
        function (){ },
        'Okay',
        'Please upload spreadsheet to proceed.',
        'Cannot proceed'
      );
      $scope.missingData = true;
      return;
    }

    $scope.state = {
      activeProject: activeProject.data,
      optimizations: []
    };

    $scope.addOptimization = function() {
      var add = function (name) {
        $scope.state.activeOptimization = {
          name: name,
          optimization_type: 'money',
          constraints: constraints,
          objectives: objectives
        };
        $scope.state.optimizations.push($scope.state.activeOptimization);
      };
      openOptimizationModal(add, 'Add optimization', $scope.state.optimizations, null, 'Add');
    };

    $http.get('/api/project/' + $scope.state.activeProject.id + '/optimizations').
      success(function (response) {
        console.log('response', response);
      });

    $scope.saveOptimization = function() {
      $http.post('/api/project/' + $scope.state.activeProject.id + '/optimizations', {
         optimization_type: $scope.state.activeOptimization.optimization_type,
         parset_id: $scope.state.activeOptimization.parset.id,
         name: $scope.state.activeOptimization.name,
         progset_id: $scope.state.activeOptimization.programSet.id,
         constraints: $scope.state.activeOptimization.constraints,
         objective: $scope.state.activeOptimization.objectives
        }).
        success(function (response) {
          console.log('response', response);
        });
    };

    // Fetch list of program-set for open-project from BE
    $http.get('/api/project/' + $scope.state.activeProject.id + '/progsets').success(function (response) {
      $scope.state.programSetList = response.progsets;
    });

    // Fetch list of parameter-set for open-project from BE
    $http.get('/api/project/' + $scope.state.activeProject.id + '/parsets').success(function (response) {
      $scope.state.parsets = response.parsets;
    });

    // Opens modal to add / rename / copy optimization
    var openOptimizationModal = function (callback, title, optimizationList, optimizationName, operation, isRename) {
      var onModalKeyDown = function (event) {
        if(event.keyCode == 27) { return modalInstance.dismiss('ESC'); }
      };
      var modalInstance = $modal.open({
        templateUrl: 'js/modules/analysis/optimization-modal.html',
        controller: ['$scope', '$document', function ($scope, $document) {
          $scope.title = title;
          $scope.name = optimizationName;
          $scope.operation = operation;
          $scope.updateOptimization = function () {
            $scope.newOptimizationName = $scope.name;
            callback($scope.name);
            modalInstance.close();
          };
          $scope.isUniqueName = function (optimizationForm) {
            var exists = _(optimizationList).some(function(item) {
                return item.name == $scope.name;
              }) && $scope.name !== optimizationName && $scope.name !== $scope.newOptimizationName;
            if(isRename) {
              optimizationForm.optimizationName.$setValidity("optimizationUpdated", $scope.name !== optimizationName);
            }
            optimizationForm.optimizationName.$setValidity("optimizationExists", !exists);
            return exists;
          };
          $document.on('keydown', onModalKeyDown); // observe
          $scope.$on('$destroy', function (){ $document.off('keydown', onModalKeyDown); });  // unobserve
        }]
      });
      return modalInstance;
    };

  });
});

// this is to be replaced by an api
var constraints = [{
  key: 'MSM programs',
  label: 'Programs for men who have sex with men',
  min: 0,
  max: undefined
},{
  key: 'HTC mobile',
  label: 'HIV testing and counseling - mobile clinics',
  min: 0,
  max: undefined
},{
  key: 'ART',
  label: 'Antiretroviral therapy',
  min: 1,
  max: undefined
},{
  key: 'VMMC',
  label: 'Voluntary medical male circumcision',
  min: 0,
  max: undefined
},{
  key: 'HTC workplace',
  label: 'HIV testing and counseling - workplace programs',
  min: 0,
  max: undefined
},{
  key: 'Condoms',
  label: 'Condom promotion and distribution',
  min: 0,
  max: undefined
},{
  key: 'PMTCT',
  label: 'Prevention of mother-to-child transmission',
  min: 0,
  max: undefined
},{
  key: 'Other',
  label: 'Other',
  min: 1,
  max: 1
},{
  key: 'MGMT',
  label: 'Management',
  min: 1,
  max: 1
},{
  key: 'HTC medical',
  label: 'HIV testing and counseling - medical facilities',
  min: 0,
  max: undefined
},{
  key: 'FSW programs',
  label: 'Programs for female sex workers and clients',
  min: 0,
  max: undefined
}];

// this is to be replaced by an api
var objectives = [{
  key: 'start',
  label: 'Year to begin optimization',
  value: 2017
},{
  key: 'end',
  label: 'Year by which to achiever objectives',
  value: 2013
},{
  key: 'budget',
  label: 'Starting budget',
  value: 63500000.0
},{
  key: 'deathweight',
  label: 'Deaths to be averted',
  value: 0
},{
  key: 'infiweight',
  label: 'Infections to be averted',
  value: 0
}];
