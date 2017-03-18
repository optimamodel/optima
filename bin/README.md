# Basic workflow

The basic workflow consists of the following:

0. `build_client.sh` -- rebuild the client, including SASS and JavaScript. Note, if you run `./build_client.sh quick`, it won't minify the JavaScript, which is much faster (10 s instead of 2 min).
0. `start_server.sh` -- start the Twisted server, which serves the main Optima website.
0. `start_celery.sh` -- start the Celery server, which handles asynchronous tasks like optimization.

# Other files

Other files are largely there for legacy purposes and are not covered yet.
