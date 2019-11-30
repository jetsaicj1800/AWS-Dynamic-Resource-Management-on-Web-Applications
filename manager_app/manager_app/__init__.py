
from flask import Flask
import threading
import signal
import boto3
import sys

webapp = Flask(__name__)
from manager_app import routes
from manager_app import s3
from manager_app.autoscaler import worker_monitor


def interrupt(a, b):
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [config.ami_id]}])

    # remove instance from the load balancer and terminate
    print("Worker termination in progress. Please wait until complete")
    for inst in instances:
        if inst.state['Name'] == 'running':
            inst.terminate()
    print("Terminated all running worker")
    sys.exit(1)


mythread = threading.Thread()
mythread = threading.Thread(target=worker_monitor)
mythread.daemon = True
mythread.start()
signal.signal(signal.SIGINT, interrupt)

