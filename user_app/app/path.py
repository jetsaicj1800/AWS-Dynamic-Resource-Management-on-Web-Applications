import os
from flask import g
import mysql.connector
import tempfile
from app import webapp
from app.config import db_config

webapp.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db


def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])


def path_generator(photo_type, name):
    # generate the path for file written

    DIR_PATH = os.path.abspath(os.getcwd())

    if name is not None:
        path = os.path.join(DIR_PATH, 'app', 'static', photo_type, name)

    else:
        path = os.path.join(DIR_PATH, 'app', 'static', photo_type)

    return path


def filename_generator(filename, username):
    name = filename.rsplit('.', 1)[0]
    file_type = filename.rsplit('.', 1)[1]

    new_name = name + "_" + username + "." + file_type

    return new_name


def filename_handler(filename):
    name = filename.rsplit('.', 1)[0]
    file_type = filename.rsplit('.', 1)[1]
    tmp_name=next(tempfile._get_candidate_names())
    new_name = tmp_name+ "." + file_type

    return new_name


def allowed_file(filename):
    image_format = {'png', 'jpg', 'jpeg', 'jpeg2000', 'tiff', 'tif', 'wav', 'gif',
                    'bmp', 'dib', 'pbm', 'pgm', 'ppm', 'pnm', 'webp', 'heif', 'heic'}

    return '.' in filename and filename.rsplit('.', 1)[1].lower() in image_format
