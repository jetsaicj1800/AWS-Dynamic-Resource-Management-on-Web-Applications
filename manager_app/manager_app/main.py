from flask import render_template, redirect, url_for, request, g
from manager_app import webapp
import boto3


#@webapp.route('/',methods=['GET'])
#@webapp.route('/index',methods=['GET'])
#@webapp.route('/main',methods=['GET'])
# Display an HTML page with links
def main():

    return redirect(url_for('ec2_list'))
    #return render_template("main.html",title="Manager-app")
