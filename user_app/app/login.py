import os
from app import webapp
from flask import render_template, redirect, url_for, g, request, session, flash, send_from_directory
from app.path import path_generator, filename_generator, get_db, connect_to_database
from werkzeug.security import generate_password_hash, check_password_hash

webapp.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


def signup_validation(username, password):
    # check if the new username is unique
    # perform registration if T, do nothing if F

    cnx = get_db()
    cursor = cnx.cursor()
    query = "SELECT user_id,password FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    query_result = cursor.fetchone()

    if query_result is not None:
        return False

    else:
        # Do user signup here using username and password
        hash_password = generate_password_hash(password)

        # store username and hash in DB
        query = "insert into users (username, password) values (%s,%s)"
        cursor.execute(query, (username, hash_password))
        cnx.commit()
        # Need to add error checking
        # Assume it works for now
        return True


def login_validation(username, password):
    # given a username and an associated password
    # check if the login info is valid
    # return T of F

    # establish the sql connection
    cnx = get_db()
    cursor = cnx.cursor()

    # perform query to see if this is indeed a register user
    # if not, redirect to the login page again
    query = "SELECT user_id,password FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    query_result = cursor.fetchone()
    if query_result is None:
        return False

    # check the provided hashed password vs hashed password from db
    hash_password = query_result[1]
    if check_password_hash(hash_password, password):
        session['username'] = request.form['username']
        return True

    else:
        return False
