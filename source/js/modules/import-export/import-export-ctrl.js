define([
  './module',
  'underscore'
], function (module, _) {
  'use strict';

  module.controller('ImportExportController', ['$scope', 'converter', function ($scope, converter) {
    /**
     * Init models
     */

    $scope.json1 = [
      {
        "_id": "53e4b085fea9cb9785672a25",
        "index": 0,
        "guid": "4edfd3eb-5316-4002-80e1-195de4c77b17",
        "isActive": false,
        "balance": "$3,672.67",
        "picture": "http://placehold.it/32x32",
        "age": 25,
        "eyeColor": "green",
        "name": "Lott Mann",
        "gender": "male",
        "company": "STROZEN",
        "email": "lottmann@strozen.com",
        "phone": "+1 (924) 539-3171",
        "address": "239 Bevy Court, Marenisco, Alabama, 7665",
        "about": "Id proident fugiat commodo nulla ad labore ullamco dolore fugiat duis tempor. Ex incididunt anim aute labore quis anim deserunt. Do anim ea excepteur est nostrud duis irure occaecat proident sunt et dolore velit. Duis non velit ea excepteur duis do aliquip mollit anim laborum sunt. Velit labore fugiat aute dolore culpa aute non eiusmod sit sunt excepteur. Nostrud nisi quis labore deserunt cillum esse ad mollit consectetur veniam magna laborum. Esse commodo labore esse ea anim elit enim ex sit id id et voluptate.\r\n",
        "registered": "2014-01-24T21:55:12 -02:00",
        "latitude": 3.578364,
        "longitude": 21.247949,
        "tags": [
          "commodo",
          "aliquip",
          "et",
          "proident",
          "Lorem",
          "sunt",
          "adipisicing"
        ],
        "friends": [
          {
            "id": 0,
            "name": "Hoover Acosta"
          },
          {
            "id": 1,
            "name": "Hopkins Russell"
          },
          {
            "id": 2,
            "name": "Lawson Sutton"
          }
        ],
        "greeting": "Hello, Lott Mann! You have 6 unread messages.",
        "favoriteFruit": "strawberry"
      },
      {
        "_id": "53e4b08529df56ba7d173d10",
        "index": 1,
        "guid": "50e12b97-98ea-4215-ab3f-d1d5cc599d06",
        "isActive": false,
        "balance": "$2,129.77",
        "picture": "http://placehold.it/32x32",
        "age": 28,
        "eyeColor": "blue",
        "name": "Lewis English",
        "gender": "male",
        "company": "GENMY",
        "email": "lewisenglish@genmy.com",
        "phone": "+1 (868) 405-3571",
        "address": "519 Cleveland Street, Noxen, California, 6955",
        "about": "Sint proident laborum occaecat commodo incididunt ex sit. Culpa excepteur ad id id consectetur quis. Qui eiusmod veniam ex dolore eiusmod nostrud mollit.\r\n",
        "registered": "2014-03-31T18:19:42 -03:00",
        "latitude": 26.702961,
        "longitude": -57.802168,
        "tags": [
          "Lorem",
          "eiusmod",
          "ullamco",
          "aliquip",
          "proident",
          "adipisicing",
          "sint"
        ],
        "friends": [
          {
            "id": 0,
            "name": "Yvette Santos"
          },
          {
            "id": 1,
            "name": "Torres Merritt"
          },
          {
            "id": 2,
            "name": "Viola Mendoza"
          }
        ],
        "greeting": "Hello, Lewis English! You have 9 unread messages.",
        "favoriteFruit": "apple"
      },
      {
        "_id": "53e4b0859fa32e8f1d53d44e",
        "index": 2,
        "guid": "f694eb41-810c-46e9-816a-734586fdb605",
        "isActive": false,
        "balance": "$3,807.46",
        "picture": "http://placehold.it/32x32",
        "age": 21,
        "eyeColor": "brown",
        "name": "Ester Wagner",
        "gender": "female",
        "company": "OVERPLEX",
        "email": "esterwagner@overplex.com",
        "phone": "+1 (911) 536-3609",
        "address": "554 Duryea Place, Shindler, Wisconsin, 2158",
        "about": "Irure voluptate ipsum aute minim. Est duis commodo magna veniam dolore reprehenderit qui aute elit dolor officia consequat ea. Minim anim duis cupidatat consectetur anim tempor ad reprehenderit nulla pariatur. Cillum consectetur dolor proident officia anim ea occaecat.\r\n",
        "registered": "2014-02-20T03:57:37 -02:00",
        "latitude": -33.212825,
        "longitude": 88.871451,
        "tags": [
          "et",
          "occaecat",
          "ad",
          "dolor",
          "laboris",
          "nostrud",
          "id"
        ],
        "friends": [
          {
            "id": 0,
            "name": "Webb Castillo"
          },
          {
            "id": 1,
            "name": "Jeannine Herman"
          },
          {
            "id": 2,
            "name": "Eve Cunningham"
          }
        ],
        "greeting": "Hello, Ester Wagner! You have 1 unread messages.",
        "favoriteFruit": "apple"
      },
      {
        "_id": "53e4b0857b28f77d92af21ad",
        "index": 3,
        "guid": "8a842450-45e0-44c2-9ad7-ad638c851975",
        "isActive": false,
        "balance": "$2,495.38",
        "picture": "http://placehold.it/32x32",
        "age": 23,
        "eyeColor": "blue",
        "name": "Bolton Lyons",
        "gender": "male",
        "company": "BUZZWORKS",
        "email": "boltonlyons@buzzworks.com",
        "phone": "+1 (963) 435-3057",
        "address": "141 Grove Place, Dupuyer, Tennessee, 1556",
        "about": "Incididunt velit ut commodo officia amet culpa proident ut veniam. Anim incididunt commodo incididunt consequat non id adipisicing. Nostrud nulla eu eiusmod qui anim magna cupidatat est.\r\n",
        "registered": "2014-07-16T11:09:30 -03:00",
        "latitude": -71.225232,
        "longitude": -176.224091,
        "tags": [
          "laboris",
          "sunt",
          "ad",
          "qui",
          "aliquip",
          "veniam",
          "occaecat"
        ],
        "friends": [
          {
            "id": 0,
            "name": "Eddie Tyler"
          },
          {
            "id": 1,
            "name": "Sharpe Cooley"
          },
          {
            "id": 2,
            "name": "Mai Ashley"
          }
        ],
        "greeting": "Hello, Bolton Lyons! You have 6 unread messages.",
        "favoriteFruit": "banana"
      },
      {
        "_id": "53e4b08509f2bd8e10b87fd2",
        "index": 4,
        "guid": "82135ea0-67f9-45fb-b2ca-39ec6f74ef03",
        "isActive": true,
        "balance": "$2,278.45",
        "picture": "http://placehold.it/32x32",
        "age": 23,
        "eyeColor": "brown",
        "name": "Hays Murphy",
        "gender": "male",
        "company": "LOVEPAD",
        "email": "haysmurphy@lovepad.com",
        "phone": "+1 (829) 591-2938",
        "address": "690 Rutledge Street, Skyland, Missouri, 7228",
        "about": "Cillum do cupidatat ut mollit qui. Veniam veniam tempor ullamco Lorem mollit elit sit duis pariatur est adipisicing laborum aute tempor. Ipsum eu fugiat culpa dolor tempor ullamco laboris nisi ad qui consequat laboris reprehenderit laboris.\r\n",
        "registered": "2014-03-16T00:41:49 -02:00",
        "latitude": -29.678843,
        "longitude": 44.447404,
        "tags": [
          "irure",
          "dolore",
          "veniam",
          "ea",
          "aliquip",
          "do",
          "exercitation"
        ],
        "friends": [
          {
            "id": 0,
            "name": "Clemons Jordan"
          },
          {
            "id": 1,
            "name": "Lela Potter"
          },
          {
            "id": 2,
            "name": "Toni Humphrey"
          }
        ],
        "greeting": "Hello, Hays Murphy! You have 5 unread messages.",
        "favoriteFruit": "banana"
      }
    ];

    $scope.cvs = converter.json2cvs($scope.json1);

//    cvs.download();
  }]);
});
