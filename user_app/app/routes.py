from flask import Response, jsonify, render_template, redirect, url_for, g, request, session, flash, send_from_directory
from app import webapp
from app.forms import LoginForm, RegisterForm
from app.path import path_generator, filename_generator, get_db, connect_to_database, allowed_file
from app.login import login_validation, signup_validation
from app.image_handle import path_save, path_to_db
from app.config import aws_config

import boto3
import requests

webapp.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
webapp.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close



@webapp.before_request
def before_request():
    try:
        response = requests.get('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
        inst_id = response.text
        cloudwatch = boto3.client('cloudwatch')
        cloudwatch.put_metric_data(
            Namespace='WORKER/EC2', MetricData =[{ 'MetricName':'HttpRequest', 'Dimensions': [{'Name': 'InstanceId','Value':inst_id}],'Unit': 'None','Value': 1.0}]
        )
    except:
        print("Not an EC2 instance")

@webapp.route('/', methods=['GET', 'POST'])
@webapp.route('/login', methods=['GET', 'POST'])
def login():
    # login function for user login page

    # retrieve username and password from the flaskform
    form = LoginForm()
    if form.sign_up.data:
        return redirect(url_for('sign_up'))

    # proceed to backend info verification if the user clicks the submit button
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # check if login is successful
        check = login_validation(username, password)

        if check:
            flash("Welcome {}".format(username))
            return redirect(url_for('upload_file'))
        else:
            flash("Invalid Username and Password")
            return redirect(url_for('login'))

    return render_template('login.html', title='Log In', form=form)


@webapp.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    # sing_up function for new user registration

    # retrieve username and password from the flaskform
    form = RegisterForm()

    # proceed to backend info verification/registration if the user clicks the submit button
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        verify_password = form.verify_password.data

        # check if passwords are the same
        if password != verify_password:
            flash("Passwords do not match")
            return render_template('signup.html', title='Sign Up', form=form)

        # check if the username is unique
        # if it is, write user info to db
        check = signup_validation(username, password)

        if check:
            flash("You have been registered. Please try to log in now")
            return redirect(url_for('login'))

        else:
            flash("Username already exists, please try a different one")
            return redirect(url_for('sign_up'))

    return render_template('signup.html', title='Sign Up', form=form)


@webapp.route('/logout')
def logout():
    # remove the username from the session if it's there
    if 'username' not in session:
        flash("You are not logged in. Please login")
        return redirect(url_for('login'))

    session.pop('username', None)
    flash("Logged out successfully")
    return redirect(url_for('login'))


@webapp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    # upload function to perform image update

    # check if there is a logged in user
    if 'username' not in session:
        flash("Please login to upload")
        return redirect(url_for('login'))

    # retrieve user info and the photo file
    if request.method == 'POST':
        username = session['username']
        file = request.files['file']

        # check if the file is in image format
        if not allowed_file(file.filename):
            flash("Invalid file type. Please select a valid image file")
            return render_template('upload.html')

        # save the photos and write associated paths to db
        check = path_to_db(file, username)

        if check:
            flash("Uploaded file successfully")
        else:
            flash("Please select a file")

    return render_template('upload.html')

@webapp.route('/display_images/<filename>', methods=['GET', 'POST'])
def display_images(filename):
    # show associated original and texted photos for a given thumbnail
    # linked to the html template page for image display

    if 'username' not in session:
        flash("Please login")
        return redirect(url_for('login'))

    s3 = boto3.client('s3')
    ori_photo = s3.generate_presigned_url('get_object',
                                    Params={'Bucket': aws_config['bucket_name'], 'Key': 'original/{}'.format(filename)},
                                    ExpiresIn=100)
    text_photo = s3.generate_presigned_url('get_object',
                                          Params={'Bucket': aws_config['bucket_name'], 'Key': 'texted/{}'.format(filename)},
                                          ExpiresIn=100)

    #old code
    #ori_photo = url_for('static', filename='original/' + filename)
    #text_photo = url_for('static', filename='texted/' + filename)

    return render_template("display.html", ori_imgURL=ori_photo, text_imgURL=text_photo)


@webapp.route('/browse', methods=['GET', 'POST'])
def browse():
    # browse thumbnails for photos that the user uploaded

    if 'username' not in session:
        flash("Please login to browse")
        return redirect(url_for('login'))



    # establish the sql connection
    username = session['username']
    cnx = get_db()
    cursor = cnx.cursor()

    # retrieve user's upload info from db
    query = "SELECT file_name, ori_path, text_path , thumb_path FROM uploads WHERE user_id = (SELECT user_id FROM users WHERE username = %s)"
    cursor.execute(query, (username,))

    s3 = boto3.client('s3')

    filename_url=[]

    file_names = [row[0] for row in cursor.fetchall()]

    for filename in file_names:
        thumbnail_url=s3.generate_presigned_url('get_object', Params = {'Bucket':aws_config['bucket_name'], 'Key':'thumbnail/{}'.format(filename)}, ExpiresIn = 100)
        filename_url.append([filename,thumbnail_url])

    return render_template("browse.html", filename_url=filename_url)


@webapp.route('/api/register', methods=['GET', 'POST'])
def register():
    # register function designed for load generator testing
    # similar as user login function

    if request.method == 'POST':

        username = request.form["username"]
        password = request.form["password"]

        if username == "" or password == "":
            response = {"status": "register-error", "text": "username or password cannot be empty"}
            return jsonify(response), 406

        if len(username) > 100 or len(password) > 100:
            response = {"status": "register-error", "text": "username or password cannot exceed 100 characters"}
            return jsonify(response), 406

        # check if the username is unique
        check = signup_validation(username, password)

        if check:
            response = {"status": "success", "text": "User registered"}
            return jsonify(response), 200
        else:
            response = {"status": "register-error", "text": "username is already in use"}
            return jsonify(response), 406


@webapp.route('/api/upload', methods=['GET', 'POST'])
def upload():
    # upload function designed for load generator testing
    # similar as user login + upload functions

    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        file = request.files['file']

        # check if login is successful
        check = login_validation(username, password)

        if not check:
            response = {"status": "login-error", "text": "Invalid username or password"}
            return jsonify(response), 401

        if not allowed_file(file.filename):
            response = {"status": "upload-error", "text": "Invalid file type"}
            return jsonify(response), 412

        # save the photos and write associated paths to db
        check = path_to_db(file, username)

        if check:
            response = {"status": "success", "text": "Image successfully uploaded"}
            return jsonify(response), 200
        else:
            response = {"status": "upload-error", "text": "Invalid file"}
            return jsonify(response), 412
