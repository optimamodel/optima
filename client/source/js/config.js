/**
 * Defines constants for application
 */
define(['angular'], function (angular) {
  'use strict';
  return angular.module('app.constants', [])
    .constant('CONFIG', {
      GRAPH_TYPES: {
        population: [
          { id: 'prev', name: 'Prevalence', byPopulation: true, total: false },
          { id: 'daly', name: 'DALYs', byPopulation: false, total: true },
          { id: 'death', name: 'Deaths', byPopulation: false, total: true },
          { id: 'inci', name: 'New infections', byPopulation: false, total: true },
          { id: 'dx', name: 'Diagnoses', byPopulation: false, total: true },
          { id: 'tx1', name: 'First-line treatment', byPopulation: false, total: true },
          { id: 'tx2', name: 'Second-line treatment', byPopulation: false, total: true }
        ],
        financial: [
          { id: 'costcur', name: 'Over Time', annual: true, cumulative: true },
          { id: 'costfut', name: 'Future', annual: true, cumulative: true },
        ]
      }
    });
});
