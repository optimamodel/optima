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
        population: [
          { id: 'prev', name: 'HIV prevalence', byPopulation: true, total: false },
          { id: 'daly', name: 'HIV-related DALYs', byPopulation: false, total: true },
          { id: 'death', name: 'HIV-related Deaths', byPopulation: false, total: true },
          { id: 'inci', name: 'New HIV infections', byPopulation: false, total: true },
          { id: 'dx', name: 'HIV diagnoses', byPopulation: false, total: true },
          { id: 'tx1', name: 'First-line treatment', byPopulation: false, total: true },
          { id: 'tx2', name: 'Second-line treatment', byPopulation: false, total: true }
        ],
        financial: [
          { id: 'costcur', name: 'Costs over time', annual: true, cumulative: true },
          { id: 'costfut', name: 'Costs for post-2015 infections', annual: true, cumulative: true },
        ]
      }
    });
});
