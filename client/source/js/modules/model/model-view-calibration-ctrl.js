define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ModelViewCalibrationController', function ($scope, $http, meta) {

    $scope.meta = meta;

    $scope.programs = _(meta.progs.long).map(function (name, index) {
      return {
        name: name,
        acronym: meta.progs.code[index]
      };
    });
    $scope.activeProgram = $scope.programs[0];

    $scope.saturationCoverageLevel = 0.9;
    $scope.fundingNeededPercent = 0.2;
    $scope.fundingNeededValue = 800000;
    $scope.behaviorWithoutMin = 1;
    $scope.behaviorWithoutMax = 1;
    $scope.behaviorWithMin = 1;
    $scope.behaviorWithMax = 1;

    $scope.generateCurves = function () {
      $http.post('/api/model/costcoverage', {
        progname: $scope.activeProgram.acronym,
        ccparams: [
          $scope.saturationCoverageLevel,
          $scope.fundingNeededPercent,
          $scope.fundingNeededValue,
          7000000
        ],
        coparams: [
          $scope.behaviorWithoutMin,
          $scope.behaviorWithoutMax,
          $scope.behaviorWithMin,
          $scope.behaviorWithMax
        ]
      }).success(function (response) {
        console.log(response);
      });
    };

    /*

     "saturation coverage level " = ccparams[0]
     "funding needed to get " = ccparams[1]
     "this program is _" = ccparams[2]
     ccparams[3] can just be set to 1

     "without this program ranges between and " = coparams[0] and coparams[1] respectively
     "under full coverage ranges between and " = coparams[2] and coparams[3] respectively

     also in lower screenshot, only have one set of 4 entry boxes -- not two sets as shown in screenshot

     Will have 3 output graphs -- the one shown in the top screenshot,
     and 2/4 shown in the bottom screenshot.
     These are plotdata_cc, plotdata_co, and plotdata respectively according to @annanachesa API

    */

  });
});
