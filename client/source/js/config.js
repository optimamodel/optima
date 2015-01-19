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
          { id: 'plhiv', name:'Number of PLHIV', byPopulation:false, total:true, stacked:false},
          { id: 'daly', name: 'HIV-related DALYs', byPopulation: false, total: true, stacked:false },
          { id: 'death', name: 'AIDS-related deaths', byPopulation: false, total: true, stacked:false },
          { id: 'inci', name: 'New HIV infections', byPopulation: false, total: true, stacked:false },
          { id: 'dx', name: 'New HIV diagnoses', byPopulation: false, total: true, stacked:false },
          { id: 'tx1', name: 'People on 1st-line treatment', byPopulation: false, total: true, stacked:false },
          { id: 'tx2', name: 'People on 2nd-line treatment', byPopulation: false, total: true, stacked:false }
        ],
        financial: [
          { id: 'costcur', name: 'Total HIV-related financial commitments', annual: true, cumulative: true },
          { id: 'costfut', name: 'Financial commitments for existing PLHIV', annual: true, cumulative: true },
        ]
      }
    });
});
