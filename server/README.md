Introduction
====

This describes the server API. For installation instructions, see the README file at the root directory level.

User API
===

These APIs allow front-end to get current user or login a user.

* `/api/user/current`

  Returns `401 Unauthorized` if user is not logged in. Otherwise this JSON:

  ```
  {
	email: "iwein@startersquad.com"
	name: "Iwein Fuld"
   }```

* `/api/user/create`

  Following data is posted when creating a new user:

  ```
  {
	email: "iwein@startersquad.com"
	name: "Iwein Fuld"
	password: 'whatever'
   }```

  On success, user is sent back this JSON:

  ```
  {
     "email": "iwein@startersquad.com",
     "name": "Iwein Fuld"
   }```

   On name already used, user is sent back this JSON:

   ```
   {
 	 status: "Username in use"
    }```

* `/api/user/login`

  Following data is posted when doing login:

  ```
	email: "iwein@startersquad.com"
	password: "whatever"
  ```

  On successful login, user is redirected to the home page.

  On login error, a 401 Unauthorized response is returned.

* `/api/user/logout`

  User is logged out and redirected back to the login page.

Project API
=====

These APIs allow front-end to work with projects.

* `/api/project/info`

  Returns `401 Unauthorized` if user is not logged in. Otherwise this JSON:

  ```
  {
	name: "Example",
	dataStart: 2000,
	dataEnd: 2015,
	projectionStartYear: 2010,
	projectionEndYear: 2030,
	programs:
	    [{"saturating": true, "short_name": "Condoms", "name": "Condom promotion and distribution"},
		 ...
		],
	populations:
		[{"name": "Female sex workers", "short_name": "FSW", "sexworker": true, "hetero": true, "injects": false, "client": false, "female": true, "homo": false, "male": false},
		 {"name": "Clients of sex workers", "short_name": "Clients", "sexworker": false, "hetero": true, "injects": false, "client": true, "female": false, "homo": false, "male": true},
		 {"name": "Men who have sex with men", "short_name": "MSM", "sexworker": false, "hetero": false, "injects": false, "client": false, "female": false, "homo": true, "male": true},
		 ...
		]
   }```
