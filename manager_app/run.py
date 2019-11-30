#!venv/bin/python
from manager_app import webapp
from manager_app import config
from manager_app.autoscaler import worker_monitor
import threading


#webapp.run(host='0.0.0.0',debug=True)


if __name__ == '__main__':

    #mythread = threading.Thread()


    #mythread = threading.Thread(target=worker_monitor)
    #mythread.start()
    #signal.signal(signal.SIGINT, interrupt)
    webapp.run(host='127.0.0.1', threaded=True)