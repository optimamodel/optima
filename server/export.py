import click
import requests
import sys
import os.path

from hashlib import sha224

@click.command()
@click.option('--old', default="http://athena.optimamodel.com")
@click.option('--username', default='test')
@click.option('--password', default='test')
def main(old, new, username, password):

    old_session = requests.Session()

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

    project_path = '%sprojects' % (user,)

    try:
        os.makedirs(project_path)
    except:
        pass

    for project in old_projects:
        click.echo("Downloading project '%s'" % (project["name"],))
        url = old + "/api/project/" + project["id"] + "/data"

        if os.path.isfile(project_path +  "/" + project["name"] + ".prj"):
            click.echo("Downloaded already, skipping...")
            continue

        download = old_session.get(url)

        with open(project_path + "/" + project["name"] + ".prj", 'wb') as f:
            f.write(download.content)


    click.echo("All downloaded! In folder %s" % (project_path,))

if __name__ == '__main__':
    main()
