import os

from flask import current_app
from validate_email import validate_email
from werkzeug.utils import secure_filename


def nullable_email(email_str):
    if not email_str:
        return email_str
    else:
        return email(email_str)

def email(email_str):
    if validate_email(email_str):
        return email_str

    raise ValueError('{} is not a valid email'.format(email_str))


def hashed_password(password_str):
    if isinstance(password_str, basestring) and len(password_str) == 56:
        return password_str

    raise ValueError('Invalid password - expecting SHA224 - Received {} of length {} and type {}'.format(
        password_str, len(password_str), type(password_str)))


def secure_filename_input(orig_name):
    return secure_filename(orig_name)


TEMPLATEDIR = "/tmp" # CK: hotfix to prevent ownership issues


def fullpath(filename, datadir=None):
    """
    "Normalizes" filename:  if it is full path, leaves it alone. Otherwise, prepends it with datadir.
    """

    if datadir == None:
        datadir = current_app.config['UPLOAD_FOLDER']

    result = filename

    # get user dir path
    datadir = upload_dir_user(datadir)

    if not(os.path.exists(datadir)):
        os.makedirs(datadir)
    if os.path.dirname(filename)=='' and not os.path.exists(filename):
        result = os.path.join(datadir, filename)

    return result


def templatepath(filename):
    return fullpath(filename, TEMPLATEDIR)


def upload_dir_user(dirpath, user_id = None):

    try:
        from flask.ext.login import current_user # pylint: disable=E0611,F0401

        # get current user
        if current_user.is_anonymous() == False:

            current_user_id = user_id if user_id else current_user.id

            # user_path
            user_path = os.path.join(dirpath, str(current_user_id))

            # if dir does not exist
            if not(os.path.exists(dirpath)):
                os.makedirs(dirpath)

            # if dir with user id does not exist
            if not(os.path.exists(user_path)):
                os.makedirs(user_path)

            return user_path
    except:
        return dirpath

    return dirpath

