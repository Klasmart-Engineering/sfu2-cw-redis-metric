import csv
import json
import boto3
import pprint
from datetime import datetime
import argparse


parser = argparse.ArgumentParser(description='generate a csv from cloudwatch and redis stats')
parser.add_argument('-p','--profile', help='AWS account', required=True)
parser.add_argument('-c','--cluster', help='ECS cluster name', required=True)
parser.add_argument('-r','--redis', help='redis stats csv', required=True)
parser.add_argument('-a','--applogs', help='cloudwatch stats csv', required=True)
args = vars(parser.parse_args())


app_logs = []
redis_logs = []
taskIds = []
taskIdDns = []

session = boto3.Session(profile_name="kl-research-global")
resource_client=session.client('ecs')


# Take ecs Task IDs and return the privateDnsName
def taskToDns(taskList):
    response = resource_client.describe_tasks(
            cluster='kl-research',
            tasks=taskList
            )
    for task in response['tasks']:
        tempTaskDetails = {}
        tempTaskArn = task['taskArn']
        tempTaskDetails['taskId'] = tempTaskArn.split("/")[2]
        attachments = task['attachments'][0]['details']
        for attachment in attachments:
            if attachment["name"] == "privateDnsName":
                tempTaskDetails['taskDns'] = attachment["value"]
        taskIdDns.append(tempTaskDetails)
    return taskIdDns

def epochMsToDate(epochMS):
    dt = datetime.utcfromtimestamp(epochMS / 1000)
    converted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
    return converted_time


# Take the csv from cloudwatch and convert the message field to a dictionary
with open(args['applogs'], newline='') as appCsv:
    appLogs = csv.DictReader(appCsv)
    for row in appLogs:
        rowDict = json.loads(row['@message']) # convert the message column into a dictionary
        app_logs.append(rowDict)
        taskIds.append(rowDict['TaskId'])


# Take the csv created from redis data and convert to list
with open(args['redis'], newline='') as redisCsv:
    redisLogs = csv.DictReader(redisCsv)
    for row in redisLogs:
        redis_logs.append(row)

# we don't need the dns entry for every line just each unique taskId
taskIds = list(set(taskIds))  #unique list of task ids
taskToDns(taskIds)


# loop through the applogs and ensure we can provide task dnsName for each taskIdDns
# If the task no longer exists then leave the dnsname blank
for app in app_logs:
    find_dns = next((x for x in taskIdDns if x["taskId"] == app["TaskId"]), None)
    if find_dns is not None:
        app["dnsName"] = find_dns["taskDns"]
    app["Datetime"] = epochMsToDate(app["Timestamp"])


# convert epoch time in the redis logs to  '%Y-%m-%d %H:%M:%S'
for log in redis_logs:
    log["Datetime"] = epochMsToDate(int(log["timestamp"]))


# loop through the cloudwatch logs and append any redis stats if available
for app in app_logs:
    for log in redis_logs:
        if app.get("dnsName") is not None:
            if app["dnsName"] == log['instance']:
                app_time = datetime.strptime(app['Datetime'], '%Y-%m-%d %H:%M:%S')
                redis_time = datetime.strptime(log['Datetime'], '%Y-%m-%d %H:%M:%S')
                # try and match logs from each file based on timestamp
                time_gap = app_time - redis_time
                gap_seconds = time_gap.total_seconds()
                if -30 <= gap_seconds <= 30:
                    app["producers"] = log['producers']
                    app["consumers"] = log['consumers']
                    app['redis_time'] = log['Datetime']

keys = ["Datetime","producers","consumers","TaskId","ServiceName","ClusterName","AvailabilityZone","Timestamp","CpuUtilized","CpuReserved","MemoryUtilized","MemoryReserved","NetworkRxBytes","NetworkRxDropped","NetworkRxErrors","NetworkRxPackets","NetworkTxBytes","NetworkTxDropped","NetworkTxErrors","NetworkTxPackets","EphemeralStorageReserved","dnsName","redis_time"]

date_object = datetime.now()
time_suffix = date_object.strftime("%Y%m%d")
output_file = time_suffix + "-results.csv"

with open(output_file, 'w', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, keys, extrasaction='ignore')
    dict_writer.writeheader()
    dict_writer.writerows(app_logs)

