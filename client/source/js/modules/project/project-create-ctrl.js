define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ProjectCreateController', function ($scope, $window) {

    $scope.populations = [
      {name: 'Female sex workers', active: false},
      {name: 'Clients of sex workers', active: false},
      {name: 'Men who have sex with men', active: false},
      {name: 'Males who inject drugs', active: false},
      {name: 'Females who inject drugs', active: false},
      {name: 'Transgender individuals', active: false},
      {name: 'Infants (0-2)', active: false},
      {name: 'Children (2-15)', active: false},
      {name: 'Young females (15-20)', active: false},
      {name: 'Young males (15-20)', active: false},
      {name: 'Adult females (20-50)', active: false},
      {name: 'Adult males (20-50)', active: false},
      {name: 'Older females (50+)', active: false},
      {name: 'Older males (50+)', active: false},
      {name: 'Other males', active: false},
      {name: 'Other females', active: false}
    ];

    $scope.programs = [
      {name: 'HIV testing & counseling', active: false},
      {name: 'Female sex workers', active: false},
      {name: 'Men who have sex with men', active: false},
      {name: 'Antiretroviral therapy', active: false},
      {name: 'Prevention of mother-to-child transmission', active: false},
      {name: 'Behavior change & communication', active: false},
      {name: 'Needle-syringe program', active: false},
      {name: 'Opiate substitution therapy', active: false},
      {name: 'Cash transfers', active: false}
    ];

    var addItemTo = function (collection, itemName) {
      collection.push({
        name: itemName,
        active: true
      });
    };

    $scope.addPopulation = function ($event) {
      $event.preventDefault();
      addItemTo($scope.populations, $scope.newPopulation);
      $scope.newPopulation = '';
    };

    $scope.addProgram = function ($event) {
      $event.preventDefault();
      addItemTo($scope.programs, $scope.newProgram);
      $scope.newProgram = '';
    };

    var toNamesArray = function (collection) {
      return _(collection).chain()
        .where({ active: true })
        .pluck('name')
        .value();
    };

    $scope.createProject = function () {
      var params = _($scope.projectParams).omit('name');
      params.programs = toNamesArray($scope.programs);
      params.populations = toNamesArray($scope.populations);
      console.log(params);

      $window.open('/api/project/create/' + $scope.projectParams.name +
      '?params=' + JSON.stringify(params));
    }

  });

});
