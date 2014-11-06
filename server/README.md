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
  
* `/api/user/login?openid=<networks open id>&next=<url to go to after login>`

  User is redirected to selected network.
  
  On successful login, user is redirected to url given in next.
  
  Examples:
  
  For Yahoo!
  
  `/api/user/login?openid=yahoo.com&next=http://optima.dev`

* `/api/user/logout`

  User is logged out. Following JSON is returned:
  
  `{
	status: "OK"
   }`
