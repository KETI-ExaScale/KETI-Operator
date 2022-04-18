#!/usr/bin/env python3
from ast import literal_eval
from ctypes import Structure
from email import message
from email.mime import image
from posixpath import split
from re import M
import re
import sys
import os
import pprint
import json
from typing_extensions import runtime
import yaml as yamlqq
import time
from datetime import datetime, timedelta, timezone
import logging
import ast

from jwt import JWT
from jwt.jwa import HS256
from jwt.jwk import jwk_from_dict
from jwt.utils import b64decode,b64encode
from spython.main import Client
from kubernetes import client, config
from protos import data_pb2_grpc
from protos import data_pb2
import grpc
import concurrent.futures
import requests


def main():
    #SlurmGetjob()
    #SlurmCreateJob()
    logging.info('test server')
    print("run serve")
    serve()

def makejwt():
    with open("/etc/slurm/jwt_hs256.key", "rb") as f:
        priv_key = f.read()

    signing_key = jwk_from_dict({
        'kty': 'oct',
        'k': b64encode(priv_key)
    })

    message = {
        "exp": int(time.time() + 10),
        "iat": int(time.time()),
        "sun": "1000"
    }

    a = JWT()
    compact_jws = a.encode(message, signing_key, alg='HS256')
    return compact_jws

def SlurmGetjob():
    newtoken = makejwt()
    req = requests.get("http://10.0.5.24:6820/slurm/v0.0.36/jobs",headers={"Content-Type":"application/json","Accept" : "application/json","X-SLURM-USER-TOKEN": newtoken, "X-SLURM-USER-NAME": "1000"})
    #print(req.json()['jobs'])
    return req

def SlurmGetNode():
    newtoken = makejwt()
    req = requests.get("http://10.0.5.24:6820/slurm/v0.0.36/nodes",headers={"Content-Type":"application/json","Accept" : "application/json","X-SLURM-USER-TOKEN": newtoken, "X-SLURM-USER-NAME": "1000"})
    return req

def SlurmGetPartition():
    newtoken = makejwt()
    req = requests.get("http://10.0.5.24:6820/slurm/v0.0.36/partitions",headers={"Content-Type":"application/json","Accept" : "application/json","X-SLURM-USER-TOKEN": newtoken, "X-SLURM-USER-NAME": "1000"})
    return req

def SlurmDeleteJob(jobid):
    newtoken = makejwt()
    #print(newtoken)
    req = requests.delete("http://10.0.5.24:6820/slurm/v0.0.36/job/" + str(jobid), headers={"Content-Type":"application/json","Accept" : "application/json","X-SLURM-USER-TOKEN": newtoken, "X-SLURM-USER-NAME": "1000"})
    return req

def SlurmCreateJob(yamldata):
    tmpdict = {"job":{"name":"","current_working_directory":"/data/NFS","standard_output":"","standard_error":"","environment": {"PATH": "/bin:/usr/bin/:/usr/local/bin/","LD_LIBRARY_PATH":
    "/lib/:/lib64/:/usr/local/lib"} },"script":""}
    jobdata = eval(str(yamldata["spec"]["containers"][0]))
    tmpdict["job"]["name"] = jobdata.get("name")
    tmpdict["job"]["current_working_directory"] = jobdata.get("current_working_diectoty","/data/NFS")
    tmpdict["job"]["standard_output"] = jobdata.get("std_output","/data/NFS/output/"+jobdata.get("name")+".out")
    tmpdict["job"]["standard_error"] = jobdata.get("std_error","/data/NFS/output/"+jobdata.get("name")+".err")
    tmpdict["script"] = "#!/bin/bash\n" + " ".join(jobdata.get("commands"))
    sendjson = json.dumps(tmpdict)
    #print(sendjson)
    newtoken = makejwt()
    req = requests.post("http://10.0.5.24:6820/slurm/v0.0.36/job/submit", headers={"Content-Type":"application/json","Accept" : "application/json","X-SLURM-USER-TOKEN": newtoken, "X-SLURM-USER-NAME": "1000"}, data= sendjson)
    #Client.load('docker://ubuntu')
    # Client.pull('docker://ketidevit2/kmc-operator-test:v24',pull_folder='/data/mountNFS', force=True) #이게 이미지 다운
    return req

def isk8s(yamldata):
    # yaml보면서 deploy인지 hpcjob인지
    yamldata = json.dumps(yamldata)
    yaml = json.loads(yamldata)
    if yaml['kind'] == 'Hpcjob':
        return False
    else:
        return True

def searchImage(filename):
    tempfilename = filename.split("/")
    filename = tempfilename[1] + ".sif"
    if os.path.isfile("/data/NFS/" + filename): #/data/NFS 등 NFS 경로를 따로 받아야함
        return 1
    else:
        return 0



def pullImage(imagename):
    Client.pull('docker://' + imagename, pull_folder='/data/NFS', force=True) #이게 이미지 다운

def Kubeclient():
    #config.load_kube_config()
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    return v1


def k8sGetPod(namespace):
    client = Kubeclient()
    podlist = client.list_namespaced_pod(namespace)
    return podlist

def k8sCreatePod(yamldata):
    namespace = getnamespace(yamldata)
    config.load_incluster_config()
    account = client.AppsV1Api()
    account.create_namespaced_deployment(namespace,body = yamldata)
    #yaml = yamldata.json()
    # yamldata = yamldata.replace('apiVersion','api_version')
    # #print(yamldata)
    # yaml = json.loads(yamldata)
    # #print(yaml)
    # spec = client.V1Deployment(**yaml)
    # print(spec)


def getnamespace(yamldata):
    #yamldata = json.dumps(yamldata)
    #yaml = json.loads(yamldata)
    # print(type(yaml))
    namespace = yamldata['metadata']['namespace']
    #print(namespace)
    return namespace

def getdeploymentname(yamldata):
    #yamldata = json.dumps(yamldata)
    #yaml = json.loads(yamldata)
    # print(type(yaml))
    name = yamldata['metadata']['name']
    # print(namespace)
    return name

def getjobname(yamldata):
    #yamldata = json.dumps(yamldata)
    #yaml = json.loads(yamldata)
    # print(type(yaml))
    jobdata = eval(str(yamldata["spec"]["containers"][0]))
    name = jobdata.get("name")
    #print(name)
    return name

def k8sDeleteDeploy(yamldata):
    namespace = getnamespace(yamldata)
    name = getdeploymentname(yamldata)
    config.load_incluster_config()
    account = client.AppsV1Api()
    ret = account.delete_namespaced_deployment(name,namespace)
    #print(ret)
    return ret

def slurmDeletejob(yamldata):
    name = getjobname(yamldata)
    joblist = SlurmGetjob()
    jobid = -1
    for i in range(len(joblist.json()['jobs'])):
        if joblist.json()['jobs'][i]['name'] == name:
            jobid = joblist.json()['jobs'][i]['job_id']
            break
    if jobid == -1:
        return 0
    else:
        SlurmDeleteJob(jobid)
        print(jobid)
        return 1

    #for i in range(len(joblist.json()['jobs'])):

    pass



def serve():
  server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
  mygrpcserver = grpcserver()
  data_pb2_grpc.add_UserServicer_to_server(mygrpcserver, server)

  server.add_insecure_port('[::]:10100')
  server.start()
  server.wait_for_termination()



class grpcserver(data_pb2_grpc.UserServicer):
    def GetJob(self, request, context):
        #print("meet get job")
        req = SlurmGetjob()
        print(req.json()['jobs'][0]['gres_detail'])
        # print(req.json()['jobs'][0]['account'])

        # jobmessage = data_pb2.JobMessage(req.text)
        # jobmessage = Structure.GetJobMessage(account="1")
        # #return data_pb2.GetJobResponse(jobmessage)
        accountdata = nodenamedata = jobstatedata = jobnamedata = startdata = standardoutdata = ""
        for i in range(len(req.json()['jobs'])) :
            accountdata = accountdata + " " + req.json()['jobs'][i]['account']
            nodenamedata = nodenamedata + " " + req.json()['jobs'][i]['nodes']
            jobstatedata = jobstatedata + " " + req.json()['jobs'][i]['job_state']
            jobnamedata = jobnamedata + " " + req.json()['jobs'][i]['name']
            startdata = startdata + " " + str(req.json()['jobs'][i]['start_time'])
            standardoutdata = standardoutdata + " " + req.json()['jobs'][i]['standard_output']


        jobdata = data_pb2.JobMessage(
            account=accountdata,
            node_name=nodenamedata,
            job_state =jobstatedata,
            job_name=jobnamedata,
            start_time=startdata,
            standard_output=standardoutdata
            
        )
        return data_pb2.GetJobResponse(get_job_message=jobdata)

    def GetPod(self, request, context):
        #print(request.name_space)
        podlist = k8sGetPod(request.name_space)
        # namespacedata = podnamedata = readydata = statusdata = restartdata = agedata = ipdata = nodenamedata = []
        namespacedata = podnamedata = readydata = statusdata = restartdata = agedata = ipdata = nodenamedata = ""
        #print(podlist.items[0].metadata.namespace)
        for i in range(len(podlist.items)):
            # namespacedata.append(podlist.items[i].metadata.namespace)
            # podnamedata.append(podlist.items[i].metadata.name)
            # readydata.append("123") #컨테이너들의 레디상태 찾아서 레디/총수량
            # statusdata.append(podlist.items[i].status.phase)
            # restartdata.append("456") #컨테이너들의 리스타트 카운트의 합?
            # agedata.append("789") #시간 job이랑 맞춰야함
            # ipdata.append(podlist.items[i].status.pod_ip)
            # nodenamedata.append(podlist.items[i].spec.node_name)
            namespacedata = namespacedata + " " + podlist.items[i].metadata.namespace
            podnamedata = podnamedata + " " + podlist.items[i].metadata.name
            readydata = readydata + " " + "123"
            statusdata = statusdata + " " + podlist.items[i].status.phase
            restartdata = restartdata + " " + "456"
            agedata = agedata + " " + "789"
            ipdata = ipdata + " " + podlist.items[i].status.pod_ip
            nodenamedata = nodenamedata + " " + podlist.items[i].spec.node_name

        poddata = data_pb2.PodMessage(
            # namespace = " ".join(namespacedata),
            # pod_name = " ".join(podnamedata),
            # ready = " ".join(readydata),
            # status = " ".join(statusdata),
            # restart = " ".join(restartdata),
            # age = " ".join(agedata),
            # ip = " ".join(ipdata),
            # node_name = " ".join(nodenamedata)
            namespace = namespacedata,
            pod_name = podnamedata,
            ready = readydata,
            status = statusdata,
            restart = restartdata,
            age = agedata,
            ip = ipdata,
            node_name = nodenamedata
        )
        return data_pb2.GetPodResponse(pod_message = poddata)

    def PostPod(self, request, context):
        # print(request.yaml_data)
        # print(type(request.yaml_data))
        yamldata = yamlqq.safe_load(request.yaml_data)
        #print(containersdata.get("image"))
        #print(json.decoder(request.yaml_data))
        if isk8s(yamldata):
            k8sCreatePod(yamldata)
        else:
            containersdata = eval(str(yamldata["spec"]["containers"][0]))
            if searchImage(containersdata.get("image")) == 0:
                pullImage(containersdata.get("image"))
            SlurmCreateJob(yamldata)

        return data_pb2.PostPodMessage()

    def GetWorkList(self, request, context):
        nowtime = time.time()
        podlist = k8sGetPod(request.namespace)
        joblist = SlurmGetjob()
        runtimedata = namespacedata = podnamedata = readydata = statusdata = restartdata = agedata = ipdata = nodenamedata = ""
        #print(podlist.items[0].metadata.namespace)
        for i in range(len(podlist.items)):
            # namespacedata.append(podlist.items[i].metadata.namespace)
            # podnamedata.append(podlist.items[i].metadata.name)
            # readydata.append("123") #컨테이너들의 레디상태 찾아서 레디/총수량
            # statusdata.append(podlist.items[i].status.phase)
            # restartdata.append("456") #컨테이너들의 리스타트 카운트의 합?
            # agedata.append("789") #시간 job이랑 맞춰야함
            # ipdata.append(podlist.items[i].status.pod_ip)
            # nodenamedata.append(podlist.items[i].spec.node_name)
            runtimedata = runtimedata + " Docker"
            namespacedata = namespacedata + " " + podlist.items[i].metadata.namespace
            podnamedata = podnamedata + " " + podlist.items[i].metadata.name
            statusdata = statusdata + " " + podlist.items[i].status.phase
            tmprestart = 0
            tmpready = 0
            for j in range(len(podlist.items[i].status.container_statuses)):
                tmprestart = tmprestart + podlist.items[i].status.container_statuses[j].restart_count
                if podlist.items[i].status.container_statuses[j].ready == 1:
                    tmpready += 1
            restartdata = restartdata + " " + str(tmprestart)
            readydata = readydata + " " + str(tmpready) + "/" + str(len(podlist.items[i].status.container_statuses))
            agedata = agedata + " " + str(int(nowtime) - int(time.mktime(podlist.items[i].status.start_time.timetuple())))
            ipdata = ipdata + " " + str(podlist.items[i].status.pod_ip)
            nodenamedata = nodenamedata + " " + podlist.items[i].spec.node_name

        for i in range(len(joblist.json()['jobs'])) :
            runtimedata = runtimedata + " Singularity"
            # accountdata = accountdata + " " + joblist.json()['jobs'][i]['account']
            nodenamedata = nodenamedata + " " + joblist.json()['jobs'][i]['batch_host']
            statusdata = statusdata + " " + joblist.json()['jobs'][i]['job_state']
            podnamedata = podnamedata + " " + joblist.json()['jobs'][i]['name']
            agedata = agedata + " " + str(int(nowtime) - int(joblist.json()['jobs'][i]['start_time']))
            namespacedata = namespacedata + " " + "-"
            restartdata = restartdata + " " + "-"
            readydata = readydata + " " + "-"
            ipdata = ipdata + " " + "-"

            # standardoutdata = standardoutdata + " " + joblist.json()['jobs'][i]['standard_output']

        worklistdata = data_pb2.WorkListMessage(
            runtime = runtimedata,
            namespace = namespacedata,
            name = podnamedata,
            ready = readydata,
            status = statusdata,
            restart = restartdata,
            age = agedata
        )
        return data_pb2.GetWorkListResponse(get_worklist_message = worklistdata)

    def DeleteWork(self, request, context):
        # 파드가 있는지 없는지부터 확인을 하고 그 담에 없으면 리턴할때 에러코드 있으면 지우고서 성공했다는 리턴
        yamldata = yamlqq.safe_load(request.yamldata)
        if isk8s(yamldata):
            ret = k8sDeleteDeploy(yamldata)
        else:
            ret = slurmDeletejob(yamldata)
        return data_pb2.DeleteWorkResponse(deletework = str(ret))

    def GetWorkName(self, request, context):
        nodename = request.nodename
        joblist = SlurmGetjob() #상태 running + 노드 이름 확인
        workdata = ""
        for i in range(len(joblist.json()['jobs'])):
            if joblist.json()['jobs'][i]['batch_host'] == nodename and joblist.json()['jobs'][i]['job_state'] == "RUNNING":
                workdata = workdata + joblist.json()['jobs'][i]['name'] + "/" + str(joblist.json()['jobs'][i]['gres_detail'][0]) + "/"+ str(joblist.json()['jobs'][i]['start_time']) + " "
        print(workdata)
        return data_pb2.GetWorkNameResponse(workname = workdata)


if __name__ == "__main__":
    main()