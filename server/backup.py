import click
import requests
import sys
import os.path
import json
from hashlib import sha224


@click.command()
@click.argument('savelocation')
@click.option('--server', default="http://hiv.optimamodel.com",
              help="Optima 2.0 server. Default: http://hiv.optimamodel.com")
@click.option('--username', default='admin',
              help="Username for logging on to the server. Default: admin")
@click.option('--password',
              help="Password for logging on to the server.")
@click.option('--overwrite', default=True, type=bool,
              help="Whether or not to overwrite local projects with server ones. Default: True.")
def main(server, username, password, overwrite, savelocation):
    """
    A utility for downloading all projects from an Optima 2.0+ server for an admin account.

    An example:
         python backup.py --username=batman --password=batcar! --server http://athena.optimamodel.com batprojects

    The command above will log into http://athena.optimamodel.com as the user
    'batman' with the password 'batcar!', and download all of that user's
    projects into the folder 'batprojects' in the current directory.

    Here's how to use it with the defaults for 'admin' at hiv.optimamodel.com, saving to folder optimaprojects:

         python backup.py --password=<secret> optimaprojects

    """

    # Make sure that we don't send duplicate /s
    if server[-1:] == "/":
        server = server[:-1]

    session = requests.Session()

    click.echo('Logging in as %s...' % (username,))
    hashed_password = sha224()
    hashed_password.update(password)
    password = hashed_password.hexdigest()

    # login to servers
    response = session.post(
        server + "/api/user/login", json={'username': username, 'password': password})
    if not response.status_code == 200:
        click.echo("Failed login:\n%s" % (response.content,))
        sys.exit(1)
    click.echo("Logged in as %s on %s" % (response.json()["username"], server))

    try:
        os.makedirs(savelocation)
    except:
        pass

    users = session.get(server + "/api/user").json()["users"]
    f = open(os.path.join(savelocation, 'users.json'), "w")
    json.dump(users, f, indent=2)
    username_by_id = {}
    for user in users:
        username_by_id[user["id"]] = user["username"]

    click.echo("Downloading projects...")
    projects = session.get(server + "/api/project/all").json()["projects"]

    for project in projects:
        username = username_by_id[project["userId"]]

        click.echo("Downloading user '%s' project '%s'" % (username, project["name"],))

        dirname = os.path.join(savelocation, username)
        try:
            os.makedirs(dirname)
        except:
            pass

        fname = os.path.join(dirname, project["name"] + ".prj")
        if os.path.isfile(fname):
            if overwrite:
                click.echo("Downloaded already, overwriting...")
            else:
                click.echo("Downloaded already, skipping (set --overwrite=True if you want to overwrite)")
                continue

        url = server + '/api/download'
        payload = {
            'name': 'download_project_with_result',
            'args': [project["id"]]
        }
        response = session.post(url, data=json.dumps(payload))
        with open(fname, 'wb') as f:
            f.write(response.content)

    click.echo("All downloaded in folder %s" % (savelocation,))


if __name__ == '__main__':
    main()
