define(
  ['./module', 'angular', 'underscore'],
  function (module, angular, _) {
  'use strict';

    // {
    //   "name": "default",
    //   "created": "Mon, 21 Mar 2016 14:04:54 GMT",
    //   "version": 2,
    //   "gaoptims": [
    //     [
    //       "5f9ac402-1a0c-468c-ae0b-5b598be6a44d",
    //       {
    //         "objectives": {
    //           "which": "outcomes",
    //           "keys": [
    //             "death",
    //             "inci"
    //           ],
    //           "keylabels": {
    //             "inci": "New infections",
    //             "death": "Deaths"
    //           },
    //           "base": null,
    //           "start": 2017,
    //           "end": 2030,
    //           "budget": 17456726.6828,
    //           "deathweight": 5,
    //           "inciweight": 1,
    //           "deathfrac": null,
    //           "incifrac": null
    //         },
    //         "resultpairs": {
    //           "98c15e0f-f9ab-44ea-95cc-9af3a2f9dcad": {
    //             "init": null,
    //             "opt": null
    //           },
    //           "85c2864c-d3c4-4af5-a3ee-7f8d7a55e42b": {
    //             "init": null,
    //             "opt": null
    //           }
    //         },
    //         "id": "5f9ac402-1a0c-468c-ae0b-5b598be6a44d",
    //         "name": "default"
    //       }
    //     ]
    //   ],
    //   "outputstring": "...",
    //   "id": "99e73475-0541-4339-b221-9459855e1783",
    //   "gitversion": "80833b5d9fa0294c3c376a79ea8adc8355cffdb0"
    // }

    module.controller(
      'PortfolioController',
      function (
        $scope, $http, activeProject, modalService, fileUpload,
        UserManager, $state, toastr) {

        function initialize() {
          $scope.objectiveKeyLabels = [
            {'key': 'start', 'label':'Start year' },
            {'key': 'end', 'label': 'End year'},
            {'key': 'budget', 'label': 'Budget'},
            {'key': 'deathweight', 'label': 'Death weight'},
            {'key': 'inciweight', 'label': 'Incidence weight'},
          ];
          $http
            .get(
              '/api/portfolio')
            .success(function(response) {
              console.log(JSON.stringify(response, null, 2));
              $scope.state = response;
            });
        }

        initialize();
      }
    );

  }
);
