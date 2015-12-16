Installation
-----

Follow the Installation Steps described in:

- client/README.md
- server/README.md
- server/db/README.md


Configuring nginx:
More often in development environment at-least we use nginx as web server. Configuring nginx for Optima is simple:

1. Installing nginx:
  - on Mac:

      use brew:

      `brew install nginx`

      after install, run:

      `sudo nginx`

  - on Ubuntu:

      `sudo apt-get install nginx`

  - on CentOS:

      `sudo yum install nginx`

2. Edit client/nginx.cong.example and replace ABSOLUTE_PATH_TO_PROJECT_SOURCE with you local Optima path
   (You can even rename this to better name like Optima_nginx.conf).

3. Enable the new configuration:
  - on Mac:

      Copy the file created in step 2 to `/usr/local/etc/nginx/servers`, or

      Go to you local nginx configuration folder (usually: `/usr/local/etc/nginx`). And open `nginx.conf`, add a line there to include the nginx configuration file for Optima like:

      ```
      server {
        ...
        include {PATH_TO_CONFIG_FILE}/optima-nginx.conf;
      }
      ```

  - on Linux:

      copy the file created in step 2 to `/etc/nginx/sites-enabled/` (or copy it to `/etc/nginx/sites-available/` and create a symlink to it from `/etc/nginx/sites-enabled/`)

4. *After any change to the configuration file* Restart nginx:
  - on Mac:

      `sudo nginx -s stop`
      `sudo nginx`

  - on Linux:

      `sudo service nginx restart`
