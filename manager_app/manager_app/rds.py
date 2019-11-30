import mysql.connector
from flask import g
from manager_app.config import db_config


def get_db():

    db = connect_to_database()
    '''
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    '''
    return db


def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])


def clear_db():
    cnx = get_db()
    cursor = cnx.cursor()
    query_users = "TRUNCATE TABLE users"
    cursor.execute(query_users)

    query_uploads = "TRUNCATE TABLE uploads"
    cursor.execute(query_uploads)

    return True

