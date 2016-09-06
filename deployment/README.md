# Optima Deployment Tooling

For full details on deployment, see http://optimamodel.com/server-notes/

## I want to...

### View the logs of an Optima service

`./service-logs.sh <service>`

Examples:

```
./service-logs.sh sandbox
./service-logs.sh sandboxcelery
```

### Update the branch

- Update the branch in `playbook.yml`
- Run `./optima-deploy.sh <service>` (e.g. `./optima-deploy.sh sandbox`)
- Run `./optima-restart.sh <service>` (e.g. `optima-restart.sh sandbox`)

### Restart Optima on Athena

`./optima-restart.sh <service>`

This will restart the main service, as well as the celery service.

Examples:

`./optima-restart.sh sandbox`
