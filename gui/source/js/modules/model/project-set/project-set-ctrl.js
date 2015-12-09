define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectSetController', function ($scope, $http, projectSetModalService, $timeout, modalService) {

    const defaultProjectSet = {name:'Default'};
    $scope.state = {
      projectSetList: [defaultProjectSet],
      activeProjectSet: defaultProjectSet
    };

    $scope.addProjectSet = function () {
      var add = function (name) {
        const addedProjectSet = {name:name};
        $scope.state.projectSetList[$scope.state.projectSetList.length] = addedProjectSet;
        $scope.state.activeProjectSet = addedProjectSet;
      };

      projectSetModalService.addProjectSet( add , $scope.state.projectSetList);
    };

    $scope.editProjectSet = function () {
      // This removing existing enter from array of projectSetList and re-adding it with updated name was needed,
      // coz it turns out that angular does not refreshes the select unless there is change in its size.
      // https://github.com/angular/angular.js/issues/10939
      var edit = function (name) {
        $scope.state.projectSetList = _.filter($scope.state.projectSetList, function(projectSet) {
          return projectSet.name !== $scope.state.activeProjectSet.name;
        });
        $timeout(function(){
          $scope.state.activeProjectSet.name = name;
          $scope.state.projectSetList[$scope.state.projectSetList.length] = $scope.state.activeProjectSet;
        });
      };
      projectSetModalService.editProjectSet($scope.state.activeProjectSet.name, edit , $scope.state.projectSetList);
    };

    $scope.deleteProjectSet = function () {
      var remove = function() {
        $scope.state.projectSetList = _.filter($scope.state.projectSetList, function(projectSet) {
          return projectSet.name !== $scope.state.activeProjectSet.name;
        });
        $scope.state.activeProjectSet = $scope.state.projectSetList ? $scope.state.projectSetList[0] : void 0;
      };
      modalService.confirm(
        function(){remove()}, function(){}, 'Yes, remove this projectSet', 'No',
        'Are you sure you want to permanently remove projectSet "' + $scope.state.activeProjectSet.name + '"?',
        'Remove projectSet'
      );
    };

    $scope.copyProjectSet = function () {
      // TODO: program details to also be copied
      var copy = function (name) {
        const copiedProjectSet = {name:name};
        $scope.state.projectSetList[$scope.state.projectSetList.length] = copiedProjectSet;
        $scope.state.activeProjectSet = copiedProjectSet;
      };
      projectSetModalService.copyProjectSet($scope.state.activeProjectSet.name, copy.bind(this) , $scope.state.projectSetList);
    };

    $scope.categories = categories;
    $scope.programs = programs;

  });
});


const categories = [
  {
    "category": "Prevention",
    "programs": [
      {
        "name": "Social and behavior change communication",
        "short_name": "SBCC"
      },
      {
        "name": "Diagnosis and treatment of sexually transmissible infections",
        "short_name": "STI"
      },
      {
        "name": "Voluntary medical male circumcision",
        "short_name": "VMMC"
      },
      {
        "name": "Programs for female sex workers and clients",
        "short_name": "FSW programs"
      },
      {
        "name": "Programs for men who have sex with men",
        "short_name": "MSM programs"
      },
      {
        "name": "Programs for people who inject drugs",
        "short_name": "PWID programs"
      },
      {
        "name": "Opiate substitution therapy",
        "short_name": "OST"
      },
      {
        "name": "Needle-syringe program",
        "short_name": "NSP"
      },
      {
        "name": "Cash transfers for HIV risk reduction",
        "short_name": "Cash transfers"
      },
      {
        "name": "Pre-exposure prophylaxis",
        "short_name": "PrEP"
      }
    ]
  },
  {
    "category": "Care and treatment",
    "programs": [
      {
        "name": "HIV testing and counseling",
        "short_name": "HTC"
      },
      {
        "name": "Antiretroviral therapy",
        "short_name": "ART"
      },
      {
        "name": "Prevention of mother-to-child transmission",
        "short_name": "PMTCT"
      },
      {
        "name": "Orphans and vulnerable children",
        "short_name": "OVC"
      },
      {
        "name": "Other care",
        "short_name": "Other care"
      }
    ]
  },
  {
    "category": "Management and administration",
    "programs": [
      {
        "name": "HR and training",
        "short_name": "HR"
      },
      {
        "name": "Enabling environment",
        "short_name": "ENV"
      }
    ]
  },
  {
    "category": "Other",
    "programs": [
      {
        "name": "Monitoring, evaluation, surveillance, and research",
        "short_name": "M&E"
      },
      {
        "name": "Health infrastructure",
        "short_name": "INFR"
      },
      {
        "name": "Other costs",
        "short_name": "Other"
      }
    ]
  }
];

const programs = [
  {
    "active": false,
    "category": "Prevention",
    "name": "Condom promotion and distribution",
    "parameters": [
      {
        "active": true,
        "value": {
          "pops": [
            ""
          ],
          "signature": [
            "condom",
            "cas"
          ]
        }
      }
    ],
    "short_name": "Condoms"
  },
  {
    "active": false,
    "category": "Prevention",
    "name": "Social and behavior change communication",
    "parameters": [
      {
        "active": true,
        "value": {
          "pops": [
            ""
          ],
          "signature": [
            "condom",
            "cas"
          ]
        }
      }
    ],
    "short_name": "SBCC"
  },
  {
    "active": false,
    "category": "Prevention",
    "name": "Diagnosis and treatment of sexually transmissible infections",
    "parameters": [
      {
        "active": true,
        "value": {
          "pops": [
            ""
          ],
          "signature": [
            "stiprevulc"
          ]
        }
      },
      {
        "active": true,
        "value": {
          "pops": [
            ""
          ],
          "signature": [
            "stiprevdis"
          ]
        }
      }
    ],
    "short_name": "STI"
  },
  {
    "active": false,
    "category": "Prevention",
    "name": "Voluntary medical male circumcision",
    "parameters": [
      {
        "active": true,
        "value": {
          "pops": [
            ""
          ],
          "signature": [
            "numcircum"
          ]
        }
      }
    ],
    "short_name": "VMMC"
  },
  {
    "active": false,
    "category": "Prevention",
    "name": "Programs for female sex workers and clients",
    "parameters": [
      {
        "active": true,
        "value": {
          "pops": [
            "FSW"
          ],
          "signature": [
            "condom",
            "com"
          ]
        }
      },
      {
        "active": true,
        "value": {
          "pops": [
            "Clients"
          ],
          "signature": [
            "condom",
            "com"
          ]
        }
      },
      {
        "active": true,
        "value": {
          "pops": [
            "FSW"
          ],
          "signature": [
            "hivtest"
          ]
        }
      }
    ],
    "short_name": "FSW programs"
  },
  {
    "active": false,
    "category": "Prevention",
    "name": "Programs for men who have sex with men",
    "parameters": [
      {
        "active": true,
        "value": {
          "pops": [
            "MSM"
          ],
          "signature": [
            "condom",
            "cas"
          ]
        }
      },
      {
        "active": true,
        "value": {
          "pops": [
            "MSM"
          ],
          "signature": [
            "hivtest"
          ]
        }
      }
    ],
    "short_name": "MSM programs"
  },
  {
    "active": false,
    "category": "Prevention",
    "name": "Programs for people who inject drugs",
    "parameters": [
      {
        "active": true,
        "value": {
          "pops": [
            "PWID"
          ],
          "signature": [
            "hivtest"
          ]
        }
      },
      {
        "active": true,
        "value": {
          "pops": [
            "PWID"
          ],
          "signature": [
            "condom",
            "cas"
          ]
        }
      }
    ],
    "short_name": "PWID programs"
  },
  {
    "active": false,
    "category": "Prevention",
    "name": "Opiate substitution therapy",
    "parameters": [
      {
        "active": true,
        "value": {
          "pops": [
            ""
          ],
          "signature": [
            "numost"
          ]
        }
      }
    ],
    "short_name": "OST"
  },
  {
    "active": false,
    "category": "Prevention",
    "name": "Needle-syringe program",
    "parameters": [
      {
        "active": true,
        "value": {
          "pops": [
            ""
          ],
          "signature": [
            "sharing"
          ]
        }
      }
    ],
    "short_name": "NSP"
  },
  {
    "active": false,
    "category": "Prevention",
    "name": "Cash transfers for HIV risk reduction",
    "parameters": [
      {
        "active": true,
        "value": {
          "pops": [
            ""
          ],
          "signature": [
            "numacts",
            "reg"
          ]
        }
      },
      {
        "active": true,
        "value": {
          "pops": [
            ""
          ],
          "signature": [
            "numacts",
            "cas"
          ]
        }
      }
    ],
    "short_name": "Cash transfers"
  },
  {
    "active": false,
    "category": "Prevention",
    "name": "Pre-exposure prophylaxis",
    "parameters": [
      {
        "active": true,
        "value": {
          "pops": [
            ""
          ],
          "signature": [
            "prep"
          ]
        }
      }
    ],
    "short_name": "PrEP"
  },
  {
    "active": false,
    "category": "Care and treatment",
    "name": "Post-exposure prophylaxis",
    "parameters": [],
    "short_name": "PEP"
  },
  {
    "active": false,
    "category": "Care and treatment",
    "name": "HIV testing and counseling",
    "parameters": [
      {
        "active": true,
        "value": {
          "pops": [
            ""
          ],
          "signature": [
            "hivtest"
          ]
        }
      }
    ],
    "short_name": "HTC"
  },
  {
    "active": false,
    "category": "Care and treatment",
    "name": "Antiretroviral therapy",
    "parameters": [
      {
        "active": true,
        "value": {
          "pops": [
            ""
          ],
          "signature": [
            "txtotal"
          ]
        }
      }
    ],
    "short_name": "ART"
  },
  {
    "active": false,
    "category": "Care and treatment",
    "name": "Prevention of mother-to-child transmission",
    "parameters": [
      {
        "active": true,
        "value": {
          "pops": [
            ""
          ],
          "signature": [
            "numpmtct"
          ]
        }
      }
    ],
    "short_name": "PMTCT"
  },
  {
    "active": false,
    "category": "Care and treatment",
    "name": "Orphans and vulnerable children",
    "parameters": [],
    "short_name": "OVC"
  },
  {
    "active": false,
    "category": "Care and treatment",
    "name": "Other care",
    "parameters": [],
    "short_name": "Other care"
  },
  {
    "active": false,
    "category": "Management and administration",
    "name": "Management",
    "parameters": [],
    "short_name": "MGMT"
  },
  {
    "active": false,
    "category": "Management and administration",
    "name": "HR and training",
    "parameters": [],
    "short_name": "HR"
  },
  {
    "active": false,
    "category": "Management and administration",
    "name": "Enabling environment",
    "parameters": [],
    "short_name": "ENV"
  },
  {
    "active": false,
    "category": "Other",
    "name": "Social protection",
    "parameters": [],
    "short_name": "SP"
  },
  {
    "active": false,
    "category": "Other",
    "name": "Monitoring, evaluation, surveillance, and research",
    "parameters": [],
    "short_name": "M&E"
  },
  {
    "active": false,
    "category": "Other",
    "name": "Health infrastructure",
    "parameters": [],
    "short_name": "INFR"
  },
  {
    "active": false,
    "category": "Other",
    "name": "Other costs",
    "parameters": [],
    "short_name": "Other"
  }
];