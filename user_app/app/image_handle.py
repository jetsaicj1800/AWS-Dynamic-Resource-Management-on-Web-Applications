from app import webapp
from werkzeug.utils import secure_filename
from app.path import path_generator, filename_generator, get_db, connect_to_database, filename_handler
from app.text_detection import detect_text
from app.generate_thumbnail import generate_thumbnail
from app.config import aws_config
import boto3

webapp.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


def path_duplicated(filename, username):
    # check if the filename already exists in the db
    # modify the filename if the same name can be found
    # return the filename (original or modified one)

    # establish the sql connection
    cnx = get_db()
    cursor = cnx.cursor(buffered=True)

    # retrieve user_id first
    query = "SELECT user_id,password FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user_id = int(cursor.fetchone()[0])

    # check if the filename exists in db
    query = "SELECT photo_id FROM uploads WHERE user_id = %s and file_name = %s"
    cursor.execute(query, (user_id, filename,))
    photo_id = cursor.fetchone()

    while photo_id is not None:
        filename = filename_handler(filename)

        # check if the filename exists in db
        query = "SELECT photo_id FROM uploads WHERE user_id = %s and file_name = %s"
        cursor.execute(query, (user_id, filename,))
        photo_id = cursor.fetchone()

    return filename


def path_save(file, username):
    # generate and save the paths for photos
    # return filename, and photo paths

    # retrieve the filename and checks if it is unique
    filename = secure_filename(file.filename)
    filename = filename_generator(filename, username)
    filename = path_duplicated(filename, username)

    # save photos (original + texted + thumbnail)
    photo_path = path_generator('original', filename)
    file.save(photo_path)

    text_path = path_generator('texted', filename)
    detect_text(photo_path, filename)

    thumb_path = path_generator('thumbnail', filename)
    generate_thumbnail(photo_path, thumb_path)

    return filename, photo_path, text_path, thumb_path


def path_to_db(file, username):
    # save the paths to the photo extensions of the submitted files
    # return True if the saving is successful , return False if the file is empty

    if file.filename is "":
        return False

    # save photos and generate paths to be saved to db
    filename, photo_path, text_path, thumb_path = path_save(file, username)

    print(text_path)

    s3 = boto3.client('s3')

    s3.upload_file(photo_path, aws_config['bucket_name'], 'original/{}'.format(filename))
    s3.upload_file(text_path, aws_config['bucket_name'], 'texted/{}'.format(filename))
    s3.upload_file(thumb_path, aws_config['bucket_name'], 'thumbnail/{}'.format(filename))


    # establish the sql connection
    cnx = get_db()
    cursor = cnx.cursor()

    # retrieve user_id for the given username
    query = "SELECT user_id,password FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user_id = int(cursor.fetchone()[0])

    # insert paths to the db
    query = "insert into uploads (user_id, file_name,ori_path,text_path,thumb_path) values (%s,%s,%s,%s,%s)"
    cursor.execute(query, (user_id, filename, photo_path, text_path, thumb_path,))

    cnx.commit()

    return True


