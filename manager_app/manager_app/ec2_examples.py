from flask import render_template, redirect, url_for, request, flash
from manager_app import webapp, config

import boto3
from manager_app.load_balancer import add_to_elb, remove_from_elb, get_workpool, get_dns, set_auto_param, get_auto_param
from manager_app.ec2_util import ec2_cpu_measure, remove_one_ec2, ec2_http_rate_measure

webapp.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


@webapp.route('/',methods=['GET'])
@webapp.route('/index',methods=['GET'])
@webapp.route('/main',methods=['GET'])
@webapp.route('/manager',methods=['GET', 'POST'])
# Display an HTML list of all ec2 instances
def ec2_list():

    # create connection to ec2
    ec2 = boto3.resource('ec2')

    #instances = ec2.instances.filter( Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

    instances = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [config.ami_id]}])

    #instances = ec2.instances.all()

    cpu_stats = {}
    http_rate_stats = {}
    for inst in instances:
        cpu_stats[inst.id] = ec2_cpu_measure(inst.id)
        http_rate_stats[inst.id] = ec2_http_rate_measure(inst.id)

    #cpu_grow, cpu_shrink, grow_ratio, shrink_ratio
    auto_params=get_auto_param()

    DNS = get_dns()

    return render_template("ec2_examples/list.html",title="Manager App",instances=instances, dns=DNS, cpu_stats=cpu_stats, http_rate_stats=http_rate_stats, auto_params=auto_params)


@webapp.route('/manager/<id>',methods=['GET'])
#Display details about a specific instance.
def ec2_view(id):
    ec2 = boto3.resource('ec2')

    instance = ec2.Instance(id)

    cpu_stats = ec2_cpu_measure(id)

    http_rate_stats = ec2_http_rate_measure(id)

    return render_template("ec2_examples/view.html",title="Instance Info",
                           instance=instance,
                           cpu_stats=cpu_stats,
                           http_rate_stats=http_rate_stats)


@webapp.route('/manager/create',methods=['POST'])
# Start a new EC2 instance
def ec2_create():

    ec2 = boto3.resource('ec2')



    command = '''#!/bin/bash 
        echo This Worked > /tmp/out.txt
        source /home/ubuntu/Desktop/a2/ECE1779-Web-Development/run.sh >> /tmp/out.txt'''

    inst_type = check_ec2_type()

    instance = ec2.create_instances(ImageId=config.ami_id, InstanceType=inst_type, MinCount=1, MaxCount=1, Monitoring={'Enabled': True}, SecurityGroupIds=['sg-0b19a38b98ffb56c9'], UserData=command)
    # InstanceType = 't1.micro' | 't2.nano' | 't2.micro' | 't2.small' | 't2.medium'

    instance[0].wait_until_running()

    add_to_elb(instance[0].id)

    instance[0].create_tags(Tags=[{'Key': 'Type', 'Value': 'worker'}])

    return redirect(url_for('ec2_list'))


@webapp.route('/manager/register/<id>',methods=['POST'])
#register ec2 to load balancer
def ec2_register(id):

    add_to_elb(id)

    return redirect(url_for('ec2_list'))


@webapp.route('/manager/deregister/<id>', methods=['POST'])
# register ec2 to load balancer
def ec2_deregister(id):

    remove_from_elb(id)

    return redirect(url_for('ec2_list'))


@webapp.route('/manager/delete/<id>',methods=['POST'])
# Terminate a EC2 instance
def ec2_destroy(id):
    # create connection to ec2
    ec2 = boto3.resource('ec2')

    remove_from_elb(id)

    ec2.instances.filter(InstanceIds=[id]).terminate()

    return redirect(url_for('ec2_list'))

@webapp.route('/manager/start/<id>',methods=['POST'])
# Restart a EC2 instance
def ec2_start(id):
    # create connection to ec2
    ec2 = boto3.resource('ec2')

    ec2.instances.filter(InstanceIds=[id]).start()

    return redirect(url_for('ec2_list'))

@webapp.route('/manager/stop/<id>',methods=['POST'])
# Restart a EC2 instance
def ec2_stop(id):
    # create connection to ec2
    ec2 = boto3.resource('ec2')

    ec2.instances.filter(InstanceIds=[id]).stop()

    return redirect(url_for('ec2_list'))

@webapp.route('/manager/shrink',methods=['POST'])
# shrink ec2 instance by one
def ec2_shrink():
    # create connection to ec2
    ec2 = boto3.resource('ec2')
    instances = get_workpool()

    removed_item = remove_one_ec2(instances)

    if len(instances) == 0:
        flash("There is no Instance Available")
        return redirect(url_for('ec2_list'))

    if removed_item != '':
        remove_from_elb(removed_item)
        ec2.instances.filter(InstanceIds=[removed_item]).terminate()
        message = "removed instance " + removed_item

    else:
        message = "Can't Shrink Anymore: Only One Instance Left in the Load Balancer"

    flash(message)
    return redirect(url_for('ec2_list'))


@webapp.route('/manager/termination', methods=['POST'])
# terminates all the workers
def ec2_termination():
    # create connection to ec2
    ec2 = boto3.resource('ec2')
    instances = get_workpool()

    #remove instance from the load balancer and terminate
    for inst in instances:
        remove_from_elb(inst[0])
        ec2.instances.filter(InstanceIds=[inst[0]]).terminate()

    flash("All workers have been terminated")
    return redirect(url_for('ec2_list'))

#route for updating autoscaler parameters
@webapp.route('/update_autoscaler', methods=['POST'])
def update_autoscaler():

    grow_threshold=request.form["GrowThreshold"]
    grow_factor = request.form["GrowFactor"]
    shrink_threshold = request.form["ShrinkThreshold"]
    shrink_factor = request.form["ShrinkFactor"]

    if(int(grow_threshold) > 100 or int(grow_threshold) < 0):
        flash("Error invalid Growth Threshold")
        return redirect(url_for('ec2_list'))

    if (int(shrink_threshold) > 100 or int(shrink_threshold) < 0):
        flash("Error invalid Shrink Threshold")
        return redirect(url_for('ec2_list'))

    if (int(grow_threshold) <= int(shrink_threshold)):
        flash("Error invalid Growth Threshold needs to greater than Shrink Threshold")
        return redirect(url_for('ec2_list'))

    new = False
    set_auto_param(grow_threshold, grow_factor, shrink_threshold, shrink_factor, new)

    return redirect(url_for('ec2_list'))


def ec2_create_multi(number):
    ec2 = boto3.resource('ec2')
    command = '''#!/bin/bash 
            echo This Worked > /tmp/out.txt
            source /home/ubuntu/Desktop/a2/ECE1779-Web-Development/run.sh >> /tmp/out.txt'''

    inst_type = check_ec2_type()

    instances = ec2.create_instances(ImageId=config.ami_id, MinCount=1, MaxCount=number, Monitoring={'Enabled': True},
                                    SecurityGroupIds=['sg-0b19a38b98ffb56c9'], UserData=command, InstanceType=inst_type)

    for inst in instances:
        inst.wait_until_running()
        add_to_elb(inst.id)

    return instances


#check whether to create tiny or small instance
def check_ec2_type():
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [config.ami_id]}])

    small_count = 0
    tiny_count = 0

    for inst in instances:

        if inst.state['Name'] == 'running':

            if inst.instance_type == 't2.small':
                small_count += 1
            else:
                tiny_count += 1

    #create tiny if small count is greater
    if small_count > tiny_count:
        return 't2.micro'
    #create small otherwise
    else:
        return 't2.small'