from manager_app.load_balancer import get_workpool, get_auto_param, remove_from_elb, set_auto_param,get_inst_health
from manager_app.ec2_util import ec2_cpu_measure_autoscale, cpu_avg_calculation, remove_one_ec2
from manager_app.routes import ec2_create_multi
from manager_app import config
from math import ceil
from time import sleep
import boto3


#main autoscaler function
def worker_monitor():
    set_auto_param(50, 2, 25, 2, False)

    #Debug message
    print('monitor initialization', flush=True)

    ec2 = boto3.resource('ec2')
    existing_workers = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [config.ami_id]}])

    # remove instance from the load balancer and terminate
    for inst in existing_workers:
        try:
            ec2.instances.filter(InstanceIds=[inst.id]).terminate()
        except:
            pass

    #create one instance as a starting point
    ec2_create_multi(1)

    #wait first instance to become healthy
    sleep(120)

    # use this for pool of created workers
    grow_pool = []

    prev_cpu = 0
    while True:

        # Run аutoscaler loop every 2 minutes minimum
        sleep(120)

        #Debug message
        print('In autoscaler loop', flush=True)

        new_workers = False

        #initalize variables for checking thresholds
        healthy_inst = 0
        total_cpu = 0


        #get autoscaler parameters from rds
        grow_threshold, shrink_threshold, grow_ratio, shrink_ratio = get_auto_param()

        #debug message
        print(grow_threshold, shrink_threshold, grow_ratio, shrink_ratio, flush=True)

        #get both healthy and unhealthy instances
        pool = get_workpool()


        # counting healthy instances and sum up their avg cpu usage
        for instance in pool:
            id = instance[0]
            status = instance[1]

            if status == 'healthy':
                inst_cpu = cpu_avg_calculation(ec2_cpu_measure_autoscale(id))
                print(inst_cpu)
                healthy_inst += 1
                if inst_cpu != 0:
                    total_cpu += inst_cpu
                else:
                    new_workers = True

        #newly created instances initializing, wait until we can measure to see actual load
        if new_workers:
            print("New instances still initializing", flush=True)
            continue

        #check if there are any healthy instances
        if healthy_inst > 0:
            message = "number of healthy instances: " + str(healthy_inst)
            print(message, flush=True)

            cpu_avg = total_cpu / healthy_inst
            print(cpu_avg)


            #heauristic to check if previously created/shrinked instances have kicked in
            #based on %change in cpu utilization

            #avoids increasing in first iteration
            if prev_cpu != 0:
                delta = abs(cpu_avg - prev_cpu)/prev_cpu

                if delta > 0.01:
                    if cpu_avg > grow_threshold:
                        #for inst in grow_pool:
                         #   print(get_inst_health(inst),flush=True)

                        grow_pool=grow(healthy_inst, grow_ratio)

                    elif cpu_avg < shrink_threshold:
                        shrink(healthy_inst, shrink_ratio, pool)

            prev_cpu = cpu_avg

        else:
            ec2_create_multi(1)
            print("No healthy instances found")




#function used to increase worker pook based on growth ratio
def grow(cur_workers, grow_ratio):

    #number of workers to create
    target_workers = cur_workers * grow_ratio - cur_workers

    #total number workers after creation
    total_worker = target_workers + cur_workers

    #limit total number of workers to 10
    if total_worker > 10:
        target_workers = 10 - cur_workers

    #create require number of workers
    instances = ec2_create_multi(target_workers)

    message = "created " + str(target_workers) + " workers"
    print(message, flush=True)


    #returning this might be useful
    return instances


#function used to shrink worker pook based on shrink ratio
def shrink(cur_workers, shrink_ratio, pool):

    ec2 = boto3.resource('ec2')

    #don't do anything if only one worker
    if cur_workers == 1:
        return True

    #number of workers to remove
    target_workers = cur_workers - ceil(cur_workers / shrink_ratio)

    #remove required number of instances from worker pool
    for i in range(target_workers):
        removed_inst = remove_one_ec2(pool)
        removed_item =removed_inst[0]
        remove_from_elb(removed_item)
        sleep(5)
        ec2.instances.filter(InstanceIds=[removed_item]).terminate()

        try:
            pool.remove(removed_inst)
        except Exception:
            pass

        message = "removed instance " + removed_item
        print(message)

    #sleep(5)

    message = "removed " + str(target_workers) + " workers"
    print(message, flush=True)

    return True
