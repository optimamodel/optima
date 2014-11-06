Installation
------------

  This component requires ([pip](http://pip.readthedocs.org/en/latest/installing.html)) and [PostgreSQL](http://www.postgresql.org/download/).

    # Configure database parameters in `src\api.py` file
    

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
  
* `/api/user/login/<networks open id>/<url to go to after login>`

  User is redirected to selected network.
  
  On successful login, user is redirected to url given in next.
  
  Examples:
  
  For Yahoo!
  
  `/api/user/login/yahoo.com/http://optima.dev`

* `/api/user/logout`

  User is logged out. Following JSON is returned:
  
  `{
	status: "OK"
   }`
