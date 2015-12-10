define([
  'angular',
  'ui.router',
  '../resources/model',
  '../resources/project',
  '../ui/type-selector/index',
  '../common/export-all-charts',
  '../common/export-all-data',
  '../validations/more-than-directive',
  '../validations/less-than-directive'
], function (angular) {
  'use strict';

  return angular.module('app.model', [
    'app.export-all-charts',
    'app.export-all-data',
    'app.resources.model',
    'app.resources.project',
    'app.ui.type-selector',
    'ui.router',
    'app.validations.more-than',
    'app.validations.less-than'
  ])
    .config(function ($stateProvider) {
      $stateProvider
        .state('model', {
          url: '/model',
          abstract: true,
          template: '<div ui-view></div>',
          resolve: {
            info: function(Project) {
              return Project.info().$promise;
            }
          }
        })
        .state('model.view', {
          url: '/view',
          templateUrl: 'js/modules/model/calibration.html',
          controller: 'ModelCalibrationController',
          resolve: {
            parameters: function (Model) {
              return Model.getCalibrateParameters().$promise;
            },
            meta: function (Model) {
              return Model.getKeyDataMeta().$promise;
            }
          }
        })
        .state('model.manageProgramSet', {
          url: '/programs',
          templateUrl: 'js/modules/model/program-set/program-set.html',
          controller: 'ProgramSetController',
          resolve: {
            availableParameters: function($http) {
              return [
                  {
                    "calibration": false,
                    "dim": 1,
                    "input_keys": [
                      "condomcom"
                    ],
                    "keys": [
                      "condom",
                      "com"
                    ],
                    "modifiable": true,
                    "name": "Condoms | Proportion of sexual acts in which condoms are used with commercial partners",
                    "page": "sex"
                  },
                  {
                    "calibration": false,
                    "dim": 1,
                    "input_keys": [
                      "condomcas"
                    ],
                    "keys": [
                      "condom",
                      "cas"
                    ],
                    "modifiable": true,
                    "name": "Condoms | Proportion of sexual acts in which condoms are used with casual partners",
                    "page": "sex"
                  },
                  {
                    "calibration": false,
                    "dim": 1,
                    "input_keys": [
                      "condomreg"
                    ],
                    "keys": [
                      "condom",
                      "reg"
                    ],
                    "modifiable": true,
                    "name": "Condoms | Proportion of sexual acts in which condoms are used with regular partners",
                    "page": "sex"
                  },
                  {
                    "calibration": false,
                    "dim": 1,
                    "input_keys": [
                      "numactscas"
                    ],
                    "keys": [
                      "numacts",
                      "cas"
                    ],
                    "modifiable": true,
                    "name": "Acts | Number of sexual acts per person per year with casual partners",
                    "page": "sex"
                  },
                  {
                    "calibration": false,
                    "dim": 1,
                    "input_keys": [
                      "numactscom"
                    ],
                    "keys": [
                      "numacts",
                      "com"
                    ],
                    "modifiable": true,
                    "name": "Acts | Number of sexual acts per person per year with commercial partners",
                    "page": "sex"
                  },
                  {
                    "calibration": false,
                    "dim": 1,
                    "input_keys": [
                      "numactsreg"
                    ],
                    "keys": [
                      "numacts",
                      "reg"
                    ],
                    "modifiable": true,
                    "name": "Acts | Number of sexual acts per person per year with regular partners",
                    "page": "sex"
                  },
                  {
                    "calibration": false,
                    "dim": 1,
                    "input_keys": [
                      "circum"
                    ],
                    "keys": [
                      "circum"
                    ],
                    "modifiable": true,
                    "name": "Circumcision | Proportion of males who are circumcised",
                    "page": "sex"
                  },
                  {
                    "calibration": false,
                    "dim": 1,
                    "input_keys": [
                      "numcircum"
                    ],
                    "keys": [
                      "numcircum"
                    ],
                    "modifiable": true,
                    "name": "Circumcision | Number of medical male circumcisions performed per year",
                    "page": "sex"
                  },
                  {
                    "calibration": false,
                    "dim": 1,
                    "input_keys": [
                      "stiprevulc"
                    ],
                    "keys": [
                      "stiprevulc"
                    ],
                    "modifiable": true,
                    "name": "STI | Prevalence of ulcerative STIs",
                    "page": "epi"
                  },
                  {
                    "calibration": false,
                    "dim": 1,
                    "input_keys": [
                      "stiprevdis"
                    ],
                    "keys": [
                      "stiprevdis"
                    ],
                    "modifiable": true,
                    "name": "STI | Prevalence of discharging STIs",
                    "page": "epi"
                  },
                  {
                    "calibration": false,
                    "dim": 1,
                    "input_keys": [
                      "hivtest"
                    ],
                    "keys": [
                      "hivtest"
                    ],
                    "modifiable": true,
                    "name": "Testing | Proportion of people who are tested for HIV each year",
                    "page": "txrx"
                  },
                  {
                    "calibration": false,
                    "dim": 1,
                    "input_keys": [
                      "hivtest"
                    ],
                    "keys": [
                      "propaware"
                    ],
                    "modifiable": true,
                    "name": "Testing | Proportion of PLHIV aware of their HIV status",
                    "page": "txrx"
                  },
                  {
                    "calibration": false,
                    "dim": 0,
                    "input_keys": [
                      "numfirstline"
                    ],
                    "keys": [
                      "txtotal"
                    ],
                    "modifiable": true,
                    "name": "Treatment | Number of PLHIV on ART",
                    "page": "txrx"
                  },
                  {
                    "calibration": false,
                    "dim": 0,
                    "input_keys": [
                      "numfirstline"
                    ],
                    "keys": [
                      "txtotal"
                    ],
                    "modifiable": true,
                    "name": "Treatment | Proportion of PLHIV on ART",
                    "page": "txrx"
                  },
                  {
                    "calibration": false,
                    "dim": 0,
                    "input_keys": [
                      "txelig"
                    ],
                    "keys": [
                      "txelig"
                    ],
                    "modifiable": true,
                    "name": "Treatment | CD4-based ART eligibility criterion",
                    "page": "txrx"
                  },
                  {
                    "calibration": false,
                    "dim": 1,
                    "input_keys": [
                      "prep"
                    ],
                    "keys": [
                      "prep"
                    ],
                    "modifiable": true,
                    "name": "PrEP | Proportion of risk encounters covered by PrEP",
                    "page": "txrx"
                  },
                  {
                    "calibration": false,
                    "dim": 1,
                    "input_keys": [
                      "numinject"
                    ],
                    "keys": [
                      "numacts",
                      "inj"
                    ],
                    "modifiable": true,
                    "name": "Injecting drug use | Number of injections per person per year",
                    "page": "inj"
                  },
                  {
                    "calibration": false,
                    "dim": 2,
                    "input_keys": [
                      "sharing"
                    ],
                    "keys": [
                      "sharing"
                    ],
                    "modifiable": true,
                    "name": "Injecting drug use | Proportion of injections using receptively shared needle-syringes",
                    "page": "inj"
                  },
                  {
                    "calibration": false,
                    "dim": 0,
                    "input_keys": [
                      "numost"
                    ],
                    "keys": [
                      "numost"
                    ],
                    "modifiable": true,
                    "name": "Injecting drug use | Proportion of people on OST",
                    "page": "inj"
                  },
                  {
                    "calibration": false,
                    "dim": 0,
                    "input_keys": [
                      "numost"
                    ],
                    "keys": [
                      "numost"
                    ],
                    "modifiable": true,
                    "name": "Injecting drug use | Number of people on OST",
                    "page": "inj"
                  },
                  {
                    "calibration": false,
                    "dim": 0,
                    "input_keys": [
                      "numpmtct"
                    ],
                    "keys": [
                      "numpmtct"
                    ],
                    "modifiable": true,
                    "name": "PMTCT | Proportion of pregnant women receiving Option B/B+",
                    "page": "txrx"
                  },
                  {
                    "calibration": false,
                    "dim": 0,
                    "input_keys": [
                      "numpmtct"
                    ],
                    "keys": [
                      "numpmtct"
                    ],
                    "modifiable": true,
                    "name": "PMTCT | Number of pregnant women receiving Option B/B+",
                    "page": "txrx"
                  },
                  {
                    "calibration": false,
                    "dim": 0,
                    "input_keys": [
                      "breast"
                    ],
                    "keys": [
                      "breast"
                    ],
                    "modifiable": true,
                    "name": "PMTCT | Proportion of mothers who breastfeed",
                    "page": "txrx"
                  }
                ];

              // return $http.get('/api/project/parameters');
            },
            predefined: function(Project) {
              return Project.predefined().$promise;
            }
          }
        })
        .state('model.define-cost-coverage-outcome', {
          url: '/define-cost-coverage-outcome',
          controller: 'ModelCostCoverageController',
          templateUrl: 'js/modules/model/cost-coverage.html',
          resolve: {
            programsResource: function(Model) {
              return Model.getPrograms().$promise;
            }
          }
        });
    });
});
