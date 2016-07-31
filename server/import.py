import click
import requests
import sys
import os.path
import glob

from hashlib import sha224

@click.command()
@click.argument('server', default="http://localhost:8080")
@click.option('--username', default='test')
@click.option('--password', default='test')
@click.option('--overwrite', default=False)
@click.argument('project_paths', nargs=-1, type=click.Path(exists=True))
def main(project_paths, server, username, password, overwrite):

    project_paths = list(set([click.format_filename(x) for x in project_paths]))
    click.echo("Preparing to upload %s projects to %s..." % (len(project_paths), server))

    new_session = requests.Session()

    click.echo('Logging in as %s...' % (username,))
    hashed_password = sha224()
    hashed_password.update(password)
    password = hashed_password.hexdigest()

    # New server login
    new_login = new_session.post(server + "/api/user/login",
                                 json={'username': username,
                                       'password': password})
    if not new_login.status_code == 200:
        click.echo("Failed login:\n%s" % (new_login.content,))
        sys.exit(1)
    click.echo("Logged in as %s on new server" % (new_login.json()["displayName"],))

    click.echo("Uploading...")
    click.echo("First, getting the projects off the new server.")

    new_projects = new_session.get(server + "/api/project").json()["projects"]
    new_project_names = [x["name"] for x in new_projects]

    projects = {x["name"]:x for x in new_projects}

    for project_path in project_paths:
        project_name = os.path.basename(project_path)[:-4]

        f = open(project_path, 'rb')

        if project_name in projects.keys():
            if overwrite:
                click.echo("will overwrite %s" % (project_name,))
                # todo!!!!!

            else:
                click.echo("NOT UPLOADING %s because --overwrite=False" % (project_name,))
                f.close()
                continue

        else:
            # New upload
            new_project_upload = new_session.post(
                server + "/api/project/data",
                data={"name": project_name},
                files={"file": (project_name + ".prj", f)})
            click.echo("Uploaded %s" % (project_name,))

        f.close()


if __name__ == '__main__':
    main()
