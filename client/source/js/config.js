/**
 * Defines constants for application
 */
define(['angular'], function (angular) {
  'use strict';
  return angular.module('app.constants', [])
    .constant('CONFIG', {
      GRAPH_MARGINS: {
        top: 20,
        right: 20,
        bottom: 45,
        left: 70
      },
      GRAPH_TYPES: {
        plotUncertainties: false,
        population: [
          { id: 'prev', name: 'HIV prevalence', byPopulation: true, total: false},
          { id: 'plhiv', name:'Number of PLHIV', byPopulation:false, total:true, stacked: true},
          { id: 'daly', name: 'HIV-related DALYs', byPopulation: false, total: true, stacked: true },
          { id: 'death', name: 'AIDS-related deaths', byPopulation: false, total: true, stacked: true },
          { id: 'inci', name: 'New HIV infections', byPopulation: false, total: true, stacked: true },
          { id: 'dx', name: 'New HIV diagnoses', byPopulation: false, total: true, stacked: true },
          { id: 'tx1', name: 'People on 1st-line treatment', byPopulation: false, total: true, stacked: true },
          { id: 'tx2', name: 'People on 2nd-line treatment', byPopulation: false, total: true, stacked: true }
        ],
        financial: [
          { id: 'total', name: 'Total HIV-related financial commitments', annual: true, cumulative: true  },
          { id: 'existing', name: 'Financial commitments for existing PLHIV', annual: true, cumulative: true },
          { id: 'future', name: 'Financial commitments for future PLHIV', annual: true, cumulative: true }
        ],
        financialAnnualCosts: [
          {id:'total', name:'total amount'},
          {id:'gdp', name:'proportion of GDP'},
          {id:'revenue', name:'proportion of government revenue'},
          {id:'govtexpend', name:'proportion of government expenditure'},
          {id:'totalhealth', name:'proportion of total health expenditure'},
          {id:'domestichealth', name:'proportion of domestic health expenditure'}
        ],
        annualCost: 'total'
      }
    });
});
