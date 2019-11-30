import boto3
from manager_app.config import load_balancer_name, TargetGroup
from manager_app.rds import get_db

#register instance with load balancer
def add_to_elb(id):
    elb = boto3.client('elbv2')
    elb.register_targets(
        TargetGroupArn=TargetGroup,
        Targets=[{'Id': id, 'Port': 5000}, ]
    )
    return True

#remove instance from load balancer pool
def remove_from_elb(id):
    elb = boto3.client('elbv2')
    elb.deregister_targets(
        TargetGroupArn=TargetGroup,
        Targets=[{'Id': id, }, ]
    )
    return True



#returns pool of healthy and unhealthy instances
def get_workpool():
    elb = boto3.client('elbv2')

    targets = elb.describe_target_health(
        TargetGroupArn=TargetGroup
    )

    instance_list = []
    for instance in targets['TargetHealthDescriptions']:

        state = instance['TargetHealth']['State']

        #only consider instances that are healthy and unhealty
        if state != 'unused' and state != 'initial' and state != 'draining':
            instance_list.append([instance['Target']['Id'], state])

    return instance_list

def get_inst_health(id):
    elb = boto3.client('elbv2')
    target=elb.describe_target_health(
        TargetGroupArn=TargetGroup,
        Targets=[{'Id':id}]
    )
    return target[0]['TargetHealth']['State']


#returns the dns of load balancer for displaying in manager app
def get_dns():
    elb = boto3.client('elbv2')

    response = elb.describe_load_balancers(
        Names=[load_balancer_name],
    )

    return response['LoadBalancers'][0]['DNSName']

#set the autoscaling parameters used in the autoscaler controlling load balancer pool
def set_auto_param(cpu_grow=50, grow_ratio=2, cpu_shrink=25, shrink_ratio=2, new=True):
    cnx = get_db()
    cursor = cnx.cursor()

    if new:
        query = "insert into auto_scaler (cpu_grow, cpu_shrink, grow_ratio, shrink_ratio) values (%s,%s,%s,%s)"

    else:
        query_check = "SELECT * FROM auto_scaler where auto_id =1"
        cursor.execute(query_check)
        query_result = cursor.fetchone()

        if query_result is None:
            query = "insert into auto_scaler (cpu_grow, cpu_shrink, grow_ratio, shrink_ratio) values (%s,%s,%s,%s)"
        else:
            query = "update auto_scaler set cpu_grow = %s, cpu_shrink = %s, grow_ratio = %s, shrink_ratio = %s where auto_id = 1"

    cursor.execute(query, (cpu_grow, cpu_shrink, grow_ratio, shrink_ratio))
    cnx.commit()

    return cpu_grow, cpu_shrink, grow_ratio, shrink_ratio

#get the autoscaling parameters used in the autoscaler controlling load balancer pool
def get_auto_param():
    cnx = get_db()
    cursor = cnx.cursor()
    query_auto_param = "SELECT cpu_grow, cpu_shrink, grow_ratio, shrink_ratio FROM auto_scaler where auto_id =1"
    cursor.execute(query_auto_param)
    query_result = cursor.fetchone()

    if query_result is None:
        cpu_grow, cpu_shrink, grow_ratio, shrink_ratio = set_auto_param()

    else:
        cpu_grow = query_result[0]
        cpu_shrink = query_result[1]
        grow_ratio = query_result[2]
        shrink_ratio = query_result[3]

    return cpu_grow, cpu_shrink, grow_ratio, shrink_ratio
