Installation
-----

Follow the Installation Steps described in:

- client/README.md
- server/README.md
- server/db/README.md


Configuring nginx:
More often in development environment at-least we use nginx as web server. Configuring nginx for Optima is simple:

1. Edit client/nginx.cong.example and replace ABSOLUTE_PATH_TO_PROJECT_SOURCE with you local Optima path
   (You can even rename this to better name like Optima_nginx.conf).

2. Go to you local nginx configuration folder, in mac its generally: `/usr/local/etc/nginx`. And open `nginx.conf`, add a line there to include the nginx configuration file for Optima like:

```
server {
  ...
  include {PATH_TO_CONFIG_FILE}/optima-nginx.conf;
}
```
