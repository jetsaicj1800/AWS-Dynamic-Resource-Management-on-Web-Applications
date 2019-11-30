import boto3
from datetime import datetime, timedelta
from operator import itemgetter

#measures the cpu usage every minutes for past 30 minutes for graphing
def ec2_cpu_measure(id):

    client = boto3.client('cloudwatch')

    metric_name = 'CPUUtilization'

    namespace = 'AWS/EC2'
    statistic = 'Average'                   # could be Sum,Maximum,Minimum,SampleCount,Average

    cpu = client.get_metric_statistics(
        Period=60,
        StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
        MetricName=metric_name,
        Namespace=namespace,  # Unit='Percent',
        Statistics=[statistic],
        Dimensions=[{'Name': 'InstanceId', 'Value': id}]
    )

    cpu_stats = []

    for point in cpu['Datapoints']:
        hour = point['Timestamp'].hour
        minute = point['Timestamp'].minute
        time = hour + minute/60
        cpu_stats.append([time,point['Average']])

    cpu_stats = sorted(cpu_stats, key=itemgetter(0))

    return cpu_stats


#measure cpu usage every minute over 2 minutes for autoscaling
def ec2_cpu_measure_autoscale(id):

    client = boto3.client('cloudwatch')

    metric_name = 'CPUUtilization'

    namespace = 'AWS/EC2'
    statistic = 'Average'                   # could be Sum,Maximum,Minimum,SampleCount,Average

    cpu = client.get_metric_statistics(
        Period=60,
        StartTime=datetime.utcnow() - timedelta(seconds=3 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
        MetricName=metric_name,
        Namespace=namespace,  # Unit='Percent',
        Statistics=[statistic],
        Dimensions=[{'Name': 'InstanceId', 'Value': id}]
    )

    cpu_stats = []

    print(len(cpu['Datapoints']))

    for point in cpu['Datapoints']:
        hour = point['Timestamp'].hour
        minute = point['Timestamp'].minute
        time = hour + minute/60
        cpu_stats.append([time,point['Average']])


    cpu_stats = sorted(cpu_stats, key=itemgetter(0))
    print(cpu_stats)
    return cpu_stats



#measure the number of http requests for each minute for the past 30 minutes
def ec2_http_rate_measure(id):

    client = boto3.client('cloudwatch')

    metric_name = 'HttpRequest'

    #namespace for instance http usage
    #use sum instead of average
    namespace = 'WORKER/EC2'
    statistic = 'Sum'  # could be Sum,Maximum,Minimum,SampleCount,Average

    http_rate = client.get_metric_statistics(
        Period=60,
        StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
        MetricName=metric_name,
        Namespace=namespace,  # Unit='Percent',
        Statistics=[statistic],
        Dimensions=[{'Name': 'InstanceId', 'Value': id}]
    )

    http_rate_stats = []

    for point in http_rate['Datapoints']:
        hour = point['Timestamp'].hour
        minute = point['Timestamp'].minute
        time = hour + minute/60
        http_rate_stats.append([time,point['Sum']])

    http_rate_stats = sorted(http_rate_stats, key=itemgetter(0))

    return http_rate_stats


def cpu_avg_calculation(cpu_stats):

    cpu_sum = 0
    for stats in cpu_stats:
        cpu_sum += stats[1]

    if len(cpu_stats) == 0:
        return 0

    else:
        return cpu_sum / len(cpu_stats)


#return an instance from a pool of instances based on lowest average cpu usage
def remove_one_ec2(instances):

    removed_item = False
    removed_cpu = 100

    if len(instances) == 1:
        return removed_item

    for inst in instances:
        cpu_avg = cpu_avg_calculation(ec2_cpu_measure(inst[0]))
        if inst[1] == 'unhealthy':
            removed_item = inst
            break
        if cpu_avg < removed_cpu and inst[1] == 'healthy':
            removed_cpu = cpu_avg
            removed_item = inst

    return removed_item



