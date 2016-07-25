import click
import requests
import sys
import os.path

from hashlib import sha224

@click.command()
@click.option('--old', default="http://athena.optimamodel.com")
@click.option('--new', default="http://localhost:8080")
@click.option('--username', default='test')
@click.option('--password', default='test')
def main(old, new, username, password):

    old_session = requests.Session()
    new_session = requests.Session()

    click.echo('Logging in as %s...' % (username,))
    hashed_password = sha224()
    hashed_password.update(password)
    password = hashed_password.hexdigest()

    # Old server login
    old_login = old_session.post(old + "/api/user/login",
                                 json={'username': username,
                                       'password': password})
    if not old_login.status_code == 200:
        click.echo("Failed login:\n%s" % (old_login.content,))
        sys.exit(1)
    click.echo("Logged in as %s on old server" % (old_login.json()["displayName"],))

    # New server login
    new_login = new_session.post(new + "/api/user/login",
                                 json={'username': username,
                                       'password': password})
    if not new_login.status_code == 200:
        click.echo("Failed login:\n%s" % (new_login.content,))
        sys.exit(1)
    click.echo("Logged in as %s on new server" % (new_login.json()["displayName"],))

    # Get the projects
    click.echo("Getting projects...")
    old_projects = old_session.get(old + "/api/project").json()["projects"]
    click.echo("Got list of %d projects." % (len(old_projects),))

    try:
        os.makedirs('projects')
    except:
        pass

    for project in old_projects:
        click.echo("Downloading project '%s'" % (project["name"],))
        url = old + "/api/project/" + project["id"] + "/data"

        if os.path.isfile("projects/" + project["name"] + ".prj"):
            click.echo("Downloaded already, skipping...")
            continue

        download = old_session.get(url)

        with open("projects/" + project["name"] + ".prj", 'wb') as f:
            f.write(download.content)


    click.echo("All downloaded! Reuploading...")
    click.echo("First, getting the projects off the new server. Same named projects will not be reuploaded.")

    new_projects = new_session.get(new + "/api/project").json()["projects"]
    new_project_names = [x["name"] for x in new_projects]

    for project in old_projects:

        if project["name"] in new_project_names:
            click.echo("%s is already on new server, skipping." % (project["name"],))
            continue

        f = open("projects/" + project["name"] + ".prj", 'rb')

        new_project_upload = new_session.post(new + "/api/project/data",
                                                  data={"name": project["name"]},
                                                  files={"file": (project["name"] + ".prj", f)})
        f.close()

        click.echo("Done with response:\n%s" % (new_project_upload.content,))


if __name__ == '__main__':
    main()
