Installation
------------

  This component requires ([pip](http://pip.readthedocs.org/en/latest/installing.html)) and [PostgreSQL](http://www.postgresql.org/download/).

    # Configure database parameters in `src\api.py` file
    app.config['DATABASE_URI'] = 'postgresql+psycopg2://optima:optima@localhost:5432/optima'

    # Run the server
    ./run.sh

User API
------------

These APIs allow front-end to get current user or login a user.

* `/api/user/current`

  Returns `401 Unauthorized` if user is not logged in. Otherwise this JSON:
  
  `{
	email: "iwein@startersquad.com"
	name: "Iwein Fuld" 
   }`

* `/api/user/create`

  Following data is posted when creating a new user:
  
  `{
	email: "iwein@startersquad.com"
	name: "Iwein Fuld"
	password: 'whatever' 
   }`
   
  On success, user is sent back this JSON:
  
  `{
	status: "OK"
   }` 
   
   On name already used, user is sent back this JSON:
   
   `{
 	 status: "Username in use"
    }`
  
* `/api/user/login`

  Following data is posted when doing login:
  
  `
	username: "iwein@startersquad.com"
	password: "whatever" 
   `
  
  On successful login, user is sent back this JSON:
  
  `{
	status: "OK"
   }`
  
  On login error, a 401 Unauthorized response is returned.

* `/api/user/logout`

  User is logged out. Following JSON is returned:
  
  `{
	status: "OK"
   }`
